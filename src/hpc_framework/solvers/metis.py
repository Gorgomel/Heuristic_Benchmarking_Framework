# src/hpc_framework/solvers/metis.py
"""Wrapper fino para `gpmetis`: mapeia β->ufactor, chama o binário e coleta artefatos."""

from __future__ import annotations

import subprocess as _stdlib_subprocess
import time
from pathlib import Path

from .common import SolverRun, ensure_tool

# Permitimos monkeypatch dos testes substituindo o atributo `subprocess` do módulo,
# mas capturamos a exceção real do stdlib para não quebrar o `except` quando há patch.
subprocess = _stdlib_subprocess
_TimeoutExpired = _stdlib_subprocess.TimeoutExpired


def _beta_to_metis_ufactor(beta: float) -> int:
    """Converte β (ex.: 0.03) no `-ufactor` esperado pelo METIS (ex.: 30)."""
    if beta < 0:
        raise ValueError("beta must be >= 0")
    # METIS usa milésimos: 0.03 -> 30
    return max(0, int(round(beta * 1000)))


def run_gpmetis(graph_path: Path, k: int, beta: float, seed: int, timeout_s: float) -> SolverRun:
    """Invoca `gpmetis` e coleta artefatos (.part.k)."""
    if k < 2:
        raise ValueError("k must be >= 2")
    if beta < 0:
        raise ValueError("beta must be >= 0")
    if not ensure_tool("gpmetis"):
        raise RuntimeError("gpmetis not found in PATH")

    ufactor = _beta_to_metis_ufactor(beta)
    out_part = Path(f"{graph_path}.part.{k}")

    cmd = ["gpmetis", str(graph_path), str(k), f"-ufactor={ufactor}", f"-seed={seed}"]

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

    except _TimeoutExpired as ex:  # capturamos a classe real, imune ao monkeypatch
        elapsed = int((time.perf_counter() - t0) * 1000)
        out = getattr(ex, "output", "") or ""
        err = getattr(ex, "stderr", "") or ""
        if isinstance(out, (bytes | bytearray)):
            out = out.decode()
        if isinstance(err, (bytes | bytearray)):
            err = err.decode()
        return SolverRun("timeout", None, None, out, err, elapsed)
