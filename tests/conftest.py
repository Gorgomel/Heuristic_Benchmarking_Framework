# tests/conftest.py
import os
import pathlib
import shutil

import pytest


@pytest.fixture(scope="session", autouse=True)
def _ensure_smoke_outdir():
    out = os.environ.get("HPC_SMOKE_OUTDIR")
    if out:
        pathlib.Path(out).mkdir(parents=True, exist_ok=True)


def _need(cmd: str):
    if shutil.which(cmd) is None:
        pytest.skip(f"{cmd} não está no PATH")


# Exemplos de uso nos testes:
# def test_metis(...):
#     _need("gpmetis")
#     ...
