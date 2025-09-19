# src/hpc_framework/solvers/kahip.py
"""Wrapper fino para `kaffpa` do KaHIP: mapeia β->imbalance, chama o binário e coleta artefatos."""

from __future__ import annotations

import subprocess as _stdlib_subprocess
import time
from pathlib import Path

from .common import SolverRun, ensure_tool

# Ver explicação análoga à do METIS.
subprocess = _stdlib_subprocess
_TimeoutExpired = _stdlib_subprocess.TimeoutExpired


def _beta_to_kahip_imbalance(beta: float) -> float:
    """Converte β (ex.: 0.03) no `--imbalance` do KaHIP (ex.: 3.000)."""
    if beta < 0:
        raise ValueError("beta must be >= 0")
    # KaHIP espera percentual: 0.03 -> 3.0
    return beta * 100.0


def run_kaffpa(
    graph_path: Path,
    k: int,
    beta: float,
    seed: int,
    timeout_s: float,
    preset: str = "fast",
) -> SolverRun:
    """Invoca `kaffpa` com `--imbalance` e coleta artefatos (.ka.part)."""
    if k < 2:
        raise ValueError("k must be >= 2")
    if beta < 0:
        raise ValueError("beta must be >= 0")
    if not ensure_tool("kaffpa"):
        raise RuntimeError("kaffpa not found in PATH")

    imb = _beta_to_kahip_imbalance(beta)
    out_part = Path(f"{graph_path}.ka.part")

    cmd = [
        "kaffpa",
        str(graph_path),
        f"--k={k}",
        f"--imbalance={imb:.3f}",
        f"--preconfiguration={preset}",
        f"--seed={seed}",
        f"--output_filename={out_part}",
    ]

    t0 = time.perf_counter()
    try:
        cp = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        elapsed = int((time.perf_counter() - t0) * 1000)
        ok = cp.returncode == 0 and out_part.exists()
        status = "ok" if ok else "error"
        return SolverRun(
            status=status,
            part_path=out_part if out_part.exists() else None,
            returncode=cp.returncode,
            stdout=cp.stdout or "",
            stderr=cp.stderr or "",
            elapsed_ms=elapsed,
        )

    except _TimeoutExpired as ex:
        elapsed = int((time.perf_counter() - t0) * 1000)
        out_raw = getattr(ex, "output", "") or ""
        err_raw = getattr(ex, "stderr", "") or ""
        if isinstance(out_raw, (bytes | bytearray)):
            out_raw = out_raw.decode()
        if isinstance(err_raw, (bytes | bytearray)):
            err_raw = err_raw.decode()
        return SolverRun("timeout", None, None, out_raw, err_raw, elapsed)
