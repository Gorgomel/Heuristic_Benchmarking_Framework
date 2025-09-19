import shutil
from pathlib import Path

import numpy as np
import pytest

from hpc_framework.runner import compute_cutsize_edges_labels, normalize_labels_zero_based
from hpc_framework.solvers.common import read_partition_labels, write_metis_graph
from hpc_framework.solvers.kahip import run_kaffpa
from hpc_framework.solvers.metis import run_gpmetis


def _tiny_graph(tmp_path: Path, n: int = 6):
    """Gera um grafinho simples (path) e salva em formato METIS .graph."""
    edges = np.array([[i, i + 1] for i in range(n - 1)], dtype=np.int64)
    gpath = tmp_path / "toy.graph"
    write_metis_graph(gpath, n=n, edges=edges)
    return gpath, edges, n


@pytest.mark.skipif(shutil.which("gpmetis") is None, reason="gpmetis não está no PATH")
def test_metis_smoke(tmp_path: Path):
    gpath, edges, n = _tiny_graph(tmp_path, n=6)

    sr = run_gpmetis(gpath, k=2, beta=0.03, seed=1, timeout_s=5.0)
    assert sr.status == "ok", f"status={sr.status}, stderr={sr.stderr!r}"
    assert sr.part_path and sr.part_path.exists()

    labels = read_partition_labels(sr.part_path)
    labels = normalize_labels_zero_based(labels)
    assert labels.size == n
    cut = compute_cutsize_edges_labels(edges, labels)
    assert isinstance(cut, int) and cut >= 0


@pytest.mark.skipif(shutil.which("kaffpa") is None, reason="kaffpa não está no PATH")
def test_kahip_smoke(tmp_path: Path):
    gpath, edges, n = _tiny_graph(tmp_path, n=6)

    sr = run_kaffpa(gpath, k=2, beta=0.03, seed=1, timeout_s=5.0, preset="fast")
    assert sr.status == "ok", f"status={sr.status}, stderr={sr.stderr!r}"
    assert sr.part_path and sr.part_path.exists()

    labels = read_partition_labels(sr.part_path)
    labels = normalize_labels_zero_based(labels)
    assert labels.size == n
    cut = compute_cutsize_edges_labels(edges, labels)
    assert isinstance(cut, int) and cut >= 0
