# tests/test_solvers_external.py
from __future__ import annotations

import json
import math
import os
import shutil
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from hpc_framework.solvers import kahip as kahip_mod
from hpc_framework.solvers import metis as metis_mod
from hpc_framework.solvers.common import read_partition_labels, write_metis_graph

# =========================
# Utilitários de teste
# =========================


def _ring_edges(n: int) -> np.ndarray:
    """Retorna arestas de um ciclo (n, 2) com dtype=int."""
    e = [[i, (i + 1) % n] for i in range(n)]
    return np.asarray(e, dtype=int)


def _cutsize(edges: np.ndarray, labels: np.ndarray) -> int:
    """Cutsize: número de arestas cruzando partições."""
    a, b = edges[:, 0], edges[:, 1]
    return int(np.sum(labels[a] != labels[b]))


def _assert_partition_ok(
    labels: np.ndarray, *, n: int, k: int, beta: float, edges: np.ndarray
) -> None:
    """Sanidade da partição: tamanho/range de rótulos, balanceamento e cutsize≥0."""
    assert labels.shape == (n,)
    assert int(labels.min()) >= 0 and int(labels.max()) < k
    counts = np.bincount(labels, minlength=k)
    max_allowed = math.ceil((1.0 + beta) * n / k)
    assert int(counts.max()) <= max_allowed
    assert _cutsize(edges, labels) >= 0


# =========================
# Artefatos & Manifesto
# =========================


def _smoke_outdir() -> Path | None:
    """Se HPC_SMOKE_OUTDIR estiver setado, retorna Path (criando diretório)."""
    root = os.getenv("HPC_SMOKE_OUTDIR")
    if not root:
        return None
    p = Path(root).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


@pytest.fixture(scope="session")
def artifact_recorder() -> Callable[..., None]:
    """Registra eventos de smoke em memória e, ao final da sessão, grava manifest.json
    em HPC_SMOKE_OUTDIR (se definido). Caso contrário, não persiste nada.
    """
    outdir = _smoke_outdir()
    events: list[dict] = []

    def _record(
        *,
        test: str,
        solver: str,
        params: dict,
        status: str,
        files: list[Path] | None = None,
        notes: str = "",
    ) -> None:
        evt = {
            "ts": time.time(),
            "ts_iso": datetime.now(UTC).isoformat(),
            "test": test,
            "solver": solver,
            "status": status,
            "params": params,
            "files": [str(Path(f).resolve()) for f in (files or [])],
            "notes": notes,
        }
        events.append(evt)

    # finalizer
    def _flush() -> None:
        if outdir and events:
            manifest = outdir / "manifest.json"
            with manifest.open("w", encoding="utf-8") as fh:
                json.dump({"events": events}, fh, indent=2, ensure_ascii=False)

    pytest.fixture(scope="session")  # silence linters about unused
    # usa addfinalizer da sessão
    import inspect

    frame = inspect.currentframe()
    # pega o request da stack do pytest (jeito simples dentro do arquivo)
    # se falhar, apenas não escreve o manifesto
    try:
        request = None
        f = frame
        while f:
            loc = f.f_locals
            if "request" in loc and getattr(loc["request"], "addfinalizer", None):
                request = loc["request"]
                break
            f = f.f_back
        if request:
            request.addfinalizer(_flush)  # type: ignore[union-attr]
    except Exception:
        pass

    return _record


def _persist(path: Path, *, prefix: str) -> Path | None:
    """Copia um arquivo para HPC_SMOKE_OUTDIR (se existir), com um prefixo no nome.
    Retorna o destino ou None se não houver outdir.
    """
    outdir = _smoke_outdir()
    if not outdir or not path.exists():
        return None
    dst = outdir / f"{prefix}_{path.name}"
    shutil.copy2(path, dst)
    return dst


# =========================
# METIS
# =========================


@pytest.mark.smoke
@pytest.mark.skipif(shutil.which("gpmetis") is None, reason="gpmetis não está no PATH")
def test_metis_smoke_and_persist(tmp_path: Path, artifact_recorder):
    n, k, beta = 50, 4, 0.03
    edges = _ring_edges(n)
    gfile = tmp_path / "toy.graph"
    write_metis_graph(gfile, n, edges)

    res = metis_mod.run_gpmetis(gfile, k=k, beta=beta, seed=1, timeout_s=10.0)
    assert res.status == "ok" and res.part_path is not None

    labels = read_partition_labels(res.part_path)
    _assert_partition_ok(labels, n=n, k=k, beta=beta, edges=edges)

    # persiste artefatos se for pedido
    copied = []
    for p in (gfile, Path(res.part_path)):  # type: ignore[arg-type]
        d = _persist(p, prefix="metis")
        if d:
            copied.append(d)

    artifact_recorder(
        test="test_metis_smoke_and_persist",
        solver="metis",
        params={"n": n, "k": k, "beta": beta, "seed": 1},
        status="ok",
        files=copied,
    )


@pytest.mark.smoke
@pytest.mark.skipif(shutil.which("gpmetis") is None, reason="gpmetis não está no PATH")
def test_metis_determinism(tmp_path: Path):
    n, k, beta = 60, 4, 0.03
    edges = _ring_edges(n)
    gfile = tmp_path / "g.graph"
    write_metis_graph(gfile, n, edges)

    r1 = metis_mod.run_gpmetis(gfile, k=k, beta=beta, seed=777, timeout_s=5.0)
    r2 = metis_mod.run_gpmetis(gfile, k=k, beta=beta, seed=777, timeout_s=5.0)
    assert r1.status == r2.status == "ok"
    l1 = read_partition_labels(r1.part_path)  # type: ignore[arg-type]
    l2 = read_partition_labels(r2.part_path)  # type: ignore[arg-type]
    assert _cutsize(edges, l1) == _cutsize(edges, l2)


def test_metis_missing_executable(monkeypatch, tmp_path: Path):
    # Simula gpmetis ausente
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError):
        metis_mod.run_gpmetis(tmp_path / "g.graph", k=2, beta=0.03, seed=1, timeout_s=1.0)


def test_metis_timeout(monkeypatch, tmp_path: Path):
    # Simula TimeoutExpired no subprocess
    import subprocess

    def _raise_timeout(*_a, **kw):
        raise subprocess.TimeoutExpired(cmd="gpmetis", timeout=kw.get("timeout", 0.01))

    monkeypatch.setattr(metis_mod, "subprocess", type("S", (), {"run": _raise_timeout}))
    g = tmp_path / "g.graph"
    write_metis_graph(g, 6, _ring_edges(6))
    res = metis_mod.run_gpmetis(g, k=2, beta=0.03, seed=1, timeout_s=0.01)
    assert res.status == "timeout" and res.part_path is None


@pytest.mark.parametrize(
    "k,beta,ok",
    [(1, 0.03, False), (3, -0.1, False), (4, 0.03, True)],
)
def test_metis_param_validation(tmp_path: Path, k: int, beta: float, ok: bool):
    n = 12
    g = tmp_path / "g.graph"
    write_metis_graph(g, n, _ring_edges(n))
    if ok:
        if shutil.which("gpmetis") is None:
            pytest.skip("gpmetis ausente")
        res = metis_mod.run_gpmetis(g, k=k, beta=beta, seed=1, timeout_s=3.0)
        assert res.status in {"ok", "error", "timeout"}
    else:
        with pytest.raises((AssertionError, ValueError)):
            metis_mod.run_gpmetis(g, k=k, beta=beta, seed=1, timeout_s=1.0)


# =========================
# KaHIP
# =========================


@pytest.mark.smoke
@pytest.mark.skipif(shutil.which("kaffpa") is None, reason="kaffpa não está no PATH")
def test_kahip_smoke_and_persist(tmp_path: Path, artifact_recorder):
    n, k, beta = 50, 4, 0.03
    edges = _ring_edges(n)
    gfile = tmp_path / "toy.graph"
    write_metis_graph(gfile, n, edges)

    res = kahip_mod.run_kaffpa(gfile, k=k, beta=beta, seed=7, timeout_s=15.0, preset="fast")
    assert res.status == "ok" and res.part_path is not None

    labels = read_partition_labels(res.part_path)
    _assert_partition_ok(labels, n=n, k=k, beta=beta, edges=edges)

    copied = []
    for p in (gfile, Path(res.part_path)):  # type: ignore[arg-type]
        d = _persist(p, prefix="kahip")
        if d:
            copied.append(d)

    artifact_recorder(
        test="test_kahip_smoke_and_persist",
        solver="kahip",
        params={"n": n, "k": k, "beta": beta, "seed": 7, "preset": "fast"},
        status="ok",
        files=copied,
    )


@pytest.mark.smoke
@pytest.mark.skipif(shutil.which("kaffpa") is None, reason="kaffpa não está no PATH")
def test_kahip_determinism(tmp_path: Path):
    n, k, beta = 60, 4, 0.03
    edges = _ring_edges(n)
    gfile = tmp_path / "g.graph"
    write_metis_graph(gfile, n, edges)

    r1 = kahip_mod.run_kaffpa(gfile, k=k, beta=beta, seed=7, timeout_s=5.0, preset="fast")
    r2 = kahip_mod.run_kaffpa(gfile, k=k, beta=beta, seed=7, timeout_s=5.0, preset="fast")
    assert r1.status == r2.status == "ok"
    l1 = read_partition_labels(r1.part_path)  # type: ignore[arg-type]
    l2 = read_partition_labels(r2.part_path)  # type: ignore[arg-type]
    assert _cutsize(edges, l1) == _cutsize(edges, l2)


def test_kahip_missing_executable(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError):
        kahip_mod.run_kaffpa(
            tmp_path / "g.graph", k=2, beta=0.03, seed=1, timeout_s=1.0, preset="fast"
        )


def test_kahip_timeout(monkeypatch, tmp_path: Path):
    import subprocess

    def _raise_timeout(*_a, **kw):
        raise subprocess.TimeoutExpired(cmd="kaffpa", timeout=kw.get("timeout", 0.01))

    monkeypatch.setattr(kahip_mod, "subprocess", type("S", (), {"run": _raise_timeout}))
    g = tmp_path / "g.graph"
    write_metis_graph(g, 6, _ring_edges(6))
    res = kahip_mod.run_kaffpa(g, k=2, beta=0.03, seed=1, timeout_s=0.01, preset="fast")
    assert res.status == "timeout" and res.part_path is None


@pytest.mark.parametrize(
    "k,beta,ok",
    [(1, 0.03, False), (3, -0.1, False), (4, 0.03, True)],
)
def test_kahip_param_validation(tmp_path: Path, k: int, beta: float, ok: bool):
    n = 12
    g = tmp_path / "g.graph"
    write_metis_graph(g, n, _ring_edges(n))
    if ok:
        if shutil.which("kaffpa") is None:
            pytest.skip("kaffpa ausente")
        res = kahip_mod.run_kaffpa(g, k=k, beta=beta, seed=1, timeout_s=3.0, preset="fast")
        assert res.status in {"ok", "error", "timeout"}
    else:
        with pytest.raises((AssertionError, ValueError)):
            kahip_mod.run_kaffpa(g, k=k, beta=beta, seed=1, timeout_s=1.0, preset="fast")
