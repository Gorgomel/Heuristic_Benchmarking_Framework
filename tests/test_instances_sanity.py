# tests/test_instances_sanity.py
from __future__ import annotations

import gzip
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

SYNTH_DIR = Path("data/instances/synthetic")


def _read_json(path: Path) -> dict[str, Any]:
    if str(path).endswith(".gz"):
        with gzip.open(path, "rt") as f:
            return json.load(f)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _iter_edges(obj: dict[str, Any]) -> Iterable[tuple[int, int]]:
    # aceita várias “formas” comuns
    for key in ("edges", "E", "edge_list"):
        xs = obj.get(key)
        if isinstance(xs, list):
            for e in xs:
                if isinstance(e, (list, tuple)) and len(e) == 2:
                    u, v = int(e[0]), int(e[1])
                    if u != v:
                        yield (u, v)
            return
    adj = obj.get("adj")
    if isinstance(adj, dict):
        for su, nbrs in adj.items():
            u = int(su)
            for v in nbrs:
                v = int(v)
                if u != v:
                    yield (u, v)


def _num_nodes(obj: dict[str, Any], edges_hint: Iterable[tuple[int, int]] | None = None) -> int:
    for k in ("n", "num_nodes"):
        if isinstance(obj.get(k), int):
            return int(obj[k])
    if edges_hint is None:
        return 0
    max_id = -1
    for u, v in edges_hint:
        if u > max_id:
            max_id = u
        if v > max_id:
            max_id = v
    return max_id + 1 if max_id >= 0 else 0


def _parse_n_from_filename(name: str) -> int | None:
    m = re.search(r"n(\d+)", name)
    return int(m.group(1)) if m else None


def test_filename_n_matches_structure_for_known_files():
    # Checagem de apenas alguns arquivos representativos (rápidos o bastante)
    for fname in [
        "n2000_p50.json.gz",
        "n2000_dense_fast.json.gz",
        "n4000_cv_high.json.gz",
        "n5000_cv_low.json.gz",
        "wilson_tree_n10000.json.gz",
    ]:
        path = SYNTH_DIR / fname
        obj = _read_json(path)
        edges = list(_iter_edges(obj))
        n_file = _parse_n_from_filename(fname)
        n_graph = _num_nodes(obj, edges)
        assert n_graph > 0
        if n_file is not None:
            # nº de nós no arquivo bate com o nome
            assert n_graph == n_file

        # Sem laços e ids válidos (checado implicitamente por _iter_edges)
        for u, v in edges:
            assert u != v
            assert 0 <= u < n_graph
            assert 0 <= v < n_graph


def test_wilson_tree_has_connected_backbone():
    """Instância 'wilson_tree_n10000' deve ser conexa e ter >= n-1 arestas únicas (UST + extras)."""
    fname = "wilson_tree_n10000.json.gz"
    path = SYNTH_DIR / fname
    obj = _read_json(path)
    edges = list(_iter_edges(obj))
    n = _num_nodes(obj, edges)

    # canoniza como arestas não direcionadas únicas
    undirected = {(u, v) if u < v else (v, u) for (u, v) in edges if u != v}
    m_unique = len(undirected)

    assert n > 0 and m_unique >= (n - 1)

    # conectividade via BFS/DFS leve (sem networkx)
    adj = [[] for _ in range(n)]
    for u, v in undirected:
        if 0 <= u < n and 0 <= v < n and u != v:
            adj[u].append(v)
            adj[v].append(u)

    seen = [False] * n
    stack = [0]
    seen[0] = True
    while stack:
        u = stack.pop()
        for w in adj[u]:
            if not seen[w]:
                seen[w] = True
                stack.append(w)

    assert all(seen), "Grafo deve ser conexo"
