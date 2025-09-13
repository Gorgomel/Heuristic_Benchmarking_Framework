"""Smoke local do kaffpa: gera grafo toy, executa e imprime labels."""

from pathlib import Path

import numpy as np

from hpc_framework.solvers.common import read_partition_labels, write_metis_graph
from hpc_framework.solvers.kahip import run_kaffpa

g = Path("/tmp/toy.graph")
write_metis_graph(g, 4, np.array([[0, 1], [1, 2], [2, 3]], dtype=int))
res = run_kaffpa(g, k=2, beta=0.03, seed=7, timeout_s=15.0, preset="fast")
print("status:", res.status, "part:", res.part_path)
if res.part_path:
    print("labels:", read_partition_labels(res.part_path))
