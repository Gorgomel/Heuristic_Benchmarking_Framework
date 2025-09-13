"""Smoke local do gpmetis: gera grafo toy, executa e imprime labels."""

from pathlib import Path

import numpy as np

from hpc_framework.solvers.common import read_partition_labels, write_metis_graph
from hpc_framework.solvers.metis import run_gpmetis

g = Path("/tmp/toy.graph")
write_metis_graph(g, 4, np.array([[0, 1], [1, 2], [2, 3]], dtype=int))
res = run_gpmetis(g, k=2, beta=0.03, seed=1, timeout_s=10.0)
print("status:", res.status, "part:", res.part_path)
if res.part_path:
    print("labels:", read_partition_labels(res.part_path))
