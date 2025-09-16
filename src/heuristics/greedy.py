"""Heurística gulosa simples (demo/smoke) com barra de progresso."""

from __future__ import annotations

# from typing import Iterable
import networkx as nx
import numpy as np

try:
    from tqdm import tqdm  # barra de progresso real, se instalado
except Exception:  # fallback: no-op, só itera

    def tqdm(x, **kwargs):
        return x


def _get_velocity(G: nx.Graph, u) -> float:
    """Retorna atributo 'velocity' se existir; caso contrário, 1.0 (fallback)."""
    return float(G.nodes[u].get("velocity", 1.0))


def run_greedy_heuristic(graph: nx.Graph, delta_v: float) -> list[set[int]]:
    """Executa heurística gulosa simples com barra de progresso.

    Args:
        graph: Grafo de entrada (NetworkX).
        delta_v: Parâmetro de sensibilidade da alocação.

    Returns:
        Uma lista de conjuntos de nós (clusters).
    """
    nodes = list(graph.nodes())
    np.random.shuffle(nodes)

    clusters: list[set[int]] = []
    assigned_nodes: set[int] = set()

    for node in tqdm(nodes, desc="Clusterização Gulosa"):
        if node in assigned_nodes:
            continue

        new_cluster = {node}
        assigned_nodes.add(node)
        frontier = list(graph.neighbors(node))
        min_vel = _get_velocity(graph, node)

        while frontier:
            v = frontier.pop()
            if v in assigned_nodes:
                continue

            if abs(_get_velocity(graph, v) - min_vel) <= delta_v:
                new_cluster.add(v)
                assigned_nodes.add(v)
                frontier.extend(graph.neighbors(v))

        clusters.append(new_cluster)

    # “Consumo” básico para smoke test (não quebra o fluxo)
    _ = sum(len(c) for c in clusters)
    return clusters
