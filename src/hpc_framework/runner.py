# src/hpc_framework/runner.py
"""Orquestrador single-run para METIS/KaHIP.
Usado pelos testes e pelo CLI para exportar .graph, invocar o solver e salvar artefatos/JSON.
"""

from __future__ import annotations

import gzip
import json
import logging
import math
import os
import platform
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from hpc_framework.solvers.common import read_partition_labels, write_metis_graph
from hpc_framework.solvers.kahip import run_kaffpa
from hpc_framework.solvers.metis import run_gpmetis


def compute_cutsize_edges_labels(edges: np.ndarray, labels: np.ndarray) -> int:
    """Cutsize: número de arestas que cruzam partições (labels diferentes)."""
    if edges.ndim != 2 or edges.shape[1] != 2:
        raise ValueError("edges must be an (m,2) array")
    u = labels[edges[:, 0]]
    v = labels[edges[:, 1]]
    return int(np.count_nonzero(u != v))


def normalize_labels_zero_based(labels: np.ndarray) -> np.ndarray:
    """Normaliza rótulos para começarem em 0 (mantendo o particionamento)."""
    lab_min = int(labels.min())
    return (labels - lab_min).astype(int, copy=False)


def feasible_beta(labels: np.ndarray, k: int, beta: float) -> tuple[bool, dict]:
    """Checa restrição de balanceamento para k-partições com folga β."""
    n = labels.shape[0]
    counts = np.bincount(labels, minlength=k)
    max_allowed = math.ceil((1.0 + beta) * n / k)
    ok = bool(np.all(counts <= max_allowed))
    return ok, {"counts": counts.tolist(), "max_allowed": max_allowed}


def extract_graph_from_instance(inst: dict[str, Any]) -> tuple[int, np.ndarray]:
    """Extrai (n, edges) de uma instância v1.1 (aceita várias chaves para n)."""
    n_raw: Any | None = inst.get("n")
    if n_raw is None:
        n_raw = inst.get("num_nodes") or inst.get("numVertices") or inst.get("num_nodes_v1_1")
    if n_raw is None:
        raise KeyError("instance missing 'n'/'num_nodes'")
    n = int(n_raw)

    edges = inst.get("edges")
    if edges is None:
        raise KeyError("instance missing 'edges'")
    edges_arr = np.asarray(edges, dtype=np.int64)
    if edges_arr.ndim != 2 or edges_arr.shape[1] != 2:
        raise ValueError("edges must be an (m,2) list/array")
    return n, edges_arr


def _read_instance(p: Path) -> dict[str, Any]:
    """Lê JSON (possivelmente .gz) de instância."""
    if str(p).endswith(".gz"):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            return json.load(f)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


@dataclass
class RunArtifact:
    """Resumo estruturado de um run único (para consumo programático)."""

    run_id: str
    algo: str
    status: str
    cut: int | None
    elapsed_ms: int
    part_file: Path | None


def run(
    *,
    instance_path: Path,
    algo: str,
    k: int,
    beta: float,
    seed: int,
    budget_time_ms: int,
    out_json: Path,
    workdir: Path,
    kahip_preset: str = "fast",
    log_level: str = "info",  # aceito (compat testes), mas sem logging verboso
) -> RunArtifact:
    """Executa um único run end-to-end e persiste JSON de saída."""
    # logging mínimo (compat)
    level = getattr(logging, (log_level or "INFO").upper(), logging.INFO)
    logging.basicConfig(level=level, stream=sys.stdout, format="[%(levelname)s] %(message)s")

    inst = _read_instance(instance_path)
    n, edges = extract_graph_from_instance(inst)

    workdir.mkdir(parents=True, exist_ok=True)
    graph_path = workdir / "graph.graph"
    write_metis_graph(graph_path, n, edges)

    t0 = time.perf_counter()
    if algo == "metis":
        res = run_gpmetis(graph_path, k=k, beta=beta, seed=seed, timeout_s=budget_time_ms / 1000.0)
    elif algo == "kahip":
        res = run_kaffpa(
            graph_path,
            k=k,
            beta=beta,
            seed=seed,
            timeout_s=budget_time_ms / 1000.0,
            preset=kahip_preset,
        )
    else:
        raise ValueError("algo must be 'metis' or 'kahip'")

    elapsed = int((time.perf_counter() - t0) * 1000)
    labels = (
        read_partition_labels(res.part_path) if res.part_path and res.part_path.exists() else None
    )
    cut = compute_cutsize_edges_labels(edges, labels) if labels is not None else None

    # Mapeia status do solver para o status esperado pelos testes de runner
    status_json = res.status if res.status in {"ok", "timeout"} else "solver_failed"

    # Persistência do JSON (apenas tipos nativos)
    out = {
        "instance_id": inst.get("instance_id", ""),
        "algo": algo,
        "k": k,
        "beta": beta,
        "seed": seed,
        "budget_time_ms": budget_time_ms,
        "workdir": str(workdir),
        "graph_path": str(graph_path),
        "status": status_json,
        "returncode": res.returncode,
        "elapsed_ms": res.elapsed_ms,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "part_path": str(res.part_path) if res.part_path else None,
        # chave exigida pelos testes:
        "cutsize_best": int(cut) if cut is not None else None,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    return RunArtifact(
        run_id=f"{algo}-{int(time.time())}",
        algo=algo,
        status=status_json,
        cut=cut,
        elapsed_ms=elapsed,
        part_file=res.part_path if res.part_path and res.part_path.exists() else None,
    )


def run_one(**kwargs):
    """Backcompat: alias para `run` (mantém assinatura esperada pelos testes/CLI)."""
    return run(**kwargs)


def _tool_version(cmd: list[str]) -> str:
    """Tenta extrair versão do tool via '--version' ou '-v'."""
    candidates = [cmd + ["--version"], cmd + ["-v"], cmd + ["-V"], cmd + ["-h"]]
    for c in candidates:
        try:
            cp = subprocess.run(c, capture_output=True, text=True, timeout=2.0, check=False)
            out = (cp.stdout or cp.stderr or "").strip()
            # heurística simples: primeira linha
            if out:
                return out.splitlines()[0][:200]
        except Exception:
            pass
    return ""


def _env_snapshot() -> dict:
    """Snapshot leve do ambiente — útil para logs/diagnóstico ad hoc."""
    py = platform.python_version()
    os_name = platform.system()
    os_rel = platform.release()
    cpu_model = platform.processor() or ""
    try:
        import psutil  # opcional

        phys = psutil.cpu_count(logical=False)
        logi = psutil.cpu_count(logical=True)
        freq = getattr(psutil.cpu_freq(), "current", None)
    except Exception:
        phys = None
        logi = os.cpu_count()
        freq = None
    return {
        "hostname": socket.gethostname(),
        "python": py,
        "os": os_name,
        "os_release": os_rel,
        "cpu": {
            "model": cpu_model,
            "cores_logical": logi,
            "cores_physical": phys,
            "freq_mhz": freq,
        },
    }


def _which(x: str) -> bool:
    """Wrapper fininho de shutil.which, mantendo assinatura antiga em alguns testes."""
    from shutil import which

    return which(x) is not None
