import numpy as np

from hpc_framework.runner import (
    _env_snapshot,
    _tool_version,
    _which,
    feasible_beta,
    normalize_labels_zero_based,
)


def test_runner_env_snapshot_and_which_and_tool_version():
    env = _env_snapshot()
    assert "python" in env and "os" in env and "cpu" in env
    assert isinstance(env["cpu"], dict)

    # 'which' deve retornar False para um comando inexistente
    assert _which("this-command-should-not-exist-xyz") is False

    # _tool_version deve retornar string (talvez vazia) sem levantar exceção
    assert isinstance(_tool_version(["python", "--version"]), str)


def test_label_utils_are_sane():
    raw = np.array([3, 3, 4, 4, 4])
    norm = normalize_labels_zero_based(raw)
    assert norm.min() == 0 and set(norm.tolist()) <= {0, 1}

    ok, info = feasible_beta(norm, k=2, beta=0.5)
    assert isinstance(ok, bool) and "counts" in info and "max_allowed" in info
    assert sum(info["counts"]) == len(raw)
