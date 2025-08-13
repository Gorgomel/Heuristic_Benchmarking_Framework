import networkx as nx
import numpy as np
from tqdm import tqdm  # <-- Adicione esta importação no topo do arquivo


def run_greedy_heuristic(graph: nx.Graph, delta_v: float):
    """
    Executa uma heurística gulosa simples para criar uma partição de clusters,
    com uma barra de progresso.
    """
    nodes = list(graph.nodes())
    np.random.shuffle(nodes)

    clusters = []
    assigned_nodes = set()

    # Envolve o loop principal com tqdm
    for node in tqdm(nodes, desc="Clusterização Gulosa"):
        if node in assigned_nodes:
            continue

        # (O resto da lógica da função permanece exatamente o mesmo)
        new_cluster = {node}
        assigned_nodes.add(node)
        frontier = list(graph.neighbors(node))
        min_vel = graph.nodes[node]["velocity"]
        max_vel = graph.nodes[node]["velocity"]

        while frontier:
            candidate = frontier.pop(0)
            if candidate in assigned_nodes:
                continue
            candidate_vel = graph.nodes[candidate]["velocity"]
            if max(max_vel, candidate_vel) - min(min_vel, candidate_vel) <= delta_v:
                new_cluster.add(candidate)
                assigned_nodes.add(candidate)
                min_vel = min(min_vel, candidate_vel)
                max_vel = max(max_vel, candidate_vel)
                for neighbor in graph.neighbors(candidate):
                    if neighbor not in assigned_nodes:
                        frontier.append(neighbor)

        clusters.append(list(new_cluster))

    # Calcular métricas
    fo1 = 0
    velocities_in_clusters = []
    for cluster in clusters:
        cluster_velocities = [graph.nodes[n]["velocity"] for n in cluster]
        min_v_in_cluster = min(cluster_velocities)
        fo1 += min_v_in_cluster * len(cluster)
        velocities_in_clusters.append(np.array(cluster_velocities))

    avg_std_dev = np.mean([v.std() for v in velocities_in_clusters if len(v) > 1])

    return {
        "fo1": fo1,
        "num_clusters": len(clusters),
        "avg_std_dev": float(avg_std_dev) if not np.isnan(avg_std_dev) else 0.0,
    }
