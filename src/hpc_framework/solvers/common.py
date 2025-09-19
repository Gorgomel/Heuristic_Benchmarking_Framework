"""Utilitários comuns para integração com solvers externos (METIS/KaHIP)."""

from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class SolverRun:
    """Resultado bruto da chamada ao solver externo."""

    status: str  # "ok" | "error" | "timeout" | "not_found"
    part_path: Path | None
    returncode: int | None
    stdout: str
    stderr: str
    elapsed_ms: int | None


def ensure_tool(name: str) -> bool:
    """True se o executável estiver no PATH."""
    return shutil.which(name) is not None


def write_metis_graph(path: Path, n: int, edges: np.ndarray) -> None:
    """Escreve grafo no formato METIS (1-based)."""
    assert edges.ndim == 2 and edges.shape[1] == 2
    adj: list[list[int]] = [[] for _ in range(n)]
    for u, v in map(tuple, edges.tolist()):
        if u == v:
            continue
        adj[u].append(v)
        adj[v].append(u)

    with path.open("w", encoding="utf-8") as f:
        m = int(sum(len(lst) for lst in adj) // 2)
        f.write(f"{n} {m}\n")
        for lst in adj:
            # 1-based (sem gerador desnecessário)
            lst_uniq = sorted({x + 1 for x in lst})
            if lst_uniq:
                f.write(" ".join(str(x) for x in lst_uniq))
            f.write("\n")


def read_partition_labels(path: Path) -> np.ndarray:
    """Lê rótulos inteiros (uma linha por vértice)."""
    labels: list[int] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                labels.append(int(s))
    return np.asarray(labels, dtype=np.int64)


def beta_to_metis_ufactor(beta: float) -> int:
    """Mapeia β (fração) para `ufactor` (permite unidades de 1/1000)."""
    if beta < 0:
        raise ValueError("beta must be >= 0")
    return int(round(beta * 1000))


def beta_to_kahip_imbalance(beta: float) -> float:
    """Mapeia β (fração) para desequilíbrio percentual do KaHIP."""
    if beta < 0:
        raise ValueError("beta must be >= 0")
    return 100.0 * beta


def run_subprocess(
    cmd: list[str],
    *,
    timeout_s: float,
) -> tuple[int | None, str, str, bool, int]:
    """Executa subprocesso capturando stdout/stderr (sempre str).

    Retorna: (returncode|None, stdout, stderr, expirou_timeout, elapsed_ms)
    """
    t0 = time.perf_counter()
    try:
        cp = subprocess.run(  # noqa: PLW1510
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        elapsed = int((time.perf_counter() - t0) * 1000)
        return cp.returncode, cp.stdout or "", cp.stderr or "", False, elapsed

    except Exception as ex:  # robusto contra monkeypatch do módulo subprocess
        elapsed = int((time.perf_counter() - t0) * 1000)
        name = ex.__class__.__name__
        # Timeout: testes monkeypatcham `metis_mod.subprocess`/`kahip_mod.subprocess`
        # para um tipo sem atributo TimeoutExpired, então não podemos referenciar
        # `subprocess.TimeoutExpired` aqui.
        if name == "TimeoutExpired":
            out_raw = getattr(ex, "output", "")
            err_raw = getattr(ex, "stderr", "")
            out = out_raw.decode() if isinstance(out_raw, bytes | bytearray) else (out_raw or "")
            err = err_raw.decode() if isinstance(err_raw, bytes | bytearray) else (err_raw or "")
            return None, out, err, True, elapsed

        # Erro genérico
        out = getattr(ex, "stdout", "")
        err = getattr(ex, "stderr", "") or str(ex)
        out_s = out.decode() if isinstance(out, bytes | bytearray) else (out or "")
        err_s = err.decode() if isinstance(err, bytes | bytearray) else (err or "")
        return 1, out_s, err_s, False, elapsed
