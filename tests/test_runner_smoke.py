import gzip
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from hpc_framework.runner import run_one


def _write_instance_edges(tmp_path: Path, n: int = 6):
    """Cria uma instância mínima com arestas explícitas e gzipa."""
    edges = np.array([[i, i + 1] for i in range(n - 1)], dtype=int).tolist()
    inst = {"instance_id": "toy", "num_nodes": n, "edges": edges}
    ipath = tmp_path / "toy.json.gz"
    with gzip.open(ipath, "wt", encoding="utf-8") as f:
        json.dump(inst, f)
    return ipath


@pytest.mark.skipif(shutil.which("gpmetis") is None, reason="gpmetis não está no PATH")
def test_runner_metis_smoke(tmp_path: Path):
    inst_path = _write_instance_edges(tmp_path, n=10)
    out_json = tmp_path / "out_metis.json"
    workdir = tmp_path / "work"

    run_one(
        instance_path=inst_path,
        algo="metis",
        k=2,
        beta=0.03,
        seed=42,
        budget_time_ms=5000,
        out_json=out_json,
        workdir=workdir,
        kahip_preset="fast",
        log_level="info",
    )

    assert out_json.exists()
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["status"] in {"ok", "timeout", "solver_failed"}
    if data["status"] == "ok":
        assert isinstance(data["cutsize_best"], int)


@pytest.mark.skipif(shutil.which("kaffpa") is None, reason="kaffpa não está no PATH")
def test_runner_kahip_smoke(tmp_path: Path):
    inst_path = _write_instance_edges(tmp_path, n=10)
    out_json = tmp_path / "out_kahip.json"
    workdir = tmp_path / "work"

    run_one(
        instance_path=inst_path,
        algo="kahip",
        k=2,
        beta=0.03,
        seed=42,
        budget_time_ms=5000,
        out_json=out_json,
        workdir=workdir,
        kahip_preset="fast",
        log_level="info",
    )

    assert out_json.exists()
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["status"] in {"ok", "timeout", "solver_failed"}
    if data["status"] == "ok":
        assert isinstance(data["cutsize_best"], int)
