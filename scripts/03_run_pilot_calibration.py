"""Script de calibração piloto (shell para rodadas rápidas e coleta de métricas)."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.generator.cli import build_graph, generate_velocities
from src.heuristics.greedy import run_greedy_heuristic

DELTA_V = 5.0


def run_calibration_scenario(nodes, density, cv_vel, seed):
    """Gera e executa um cenário, imprimindo as métricas resultantes."""
    print(f"\n--- Cenário: Nós={nodes}, Densidade={density}, CV={cv_vel} ---")
    rng = np.random.default_rng(seed)

    graph, actual_density = build_graph(rng, num_nodes=nodes, requested_density=density)

    actual_nodes = graph.number_of_nodes()
    velocities = generate_velocities(rng, actual_nodes, cv_vel)

    for i, node in enumerate(graph.nodes()):
        graph.nodes[node]["velocity"] = velocities[i]

    metrics = run_greedy_heuristic(graph, DELTA_V)

    print(f"FO1: {metrics['fo1']:.2f}")
    print(f"Número de Clusters: {metrics['num_clusters']}")
    print(f"Desvio Padrão Médio Intra-Cluster: {metrics['avg_std_dev']:.2f}")
    return metrics


if __name__ == "__main__":
    print("Iniciando execuções piloto para calibrar bounds.json...")

    # Cenário 1: Pequeno e Esparso (tende a gerar mais clusters)
    run_calibration_scenario(nodes=100, density=0.05, cv_vel=0.1, seed=1)

    # Cenário 2: Grande e Denso (tende a gerar menos clusters e FO1 maior)
    run_calibration_scenario(nodes=5000, density=0.3, cv_vel=0.4, seed=2)

    print("\nAnálise concluída. Use os valores MÁXIMOS observados para atualizar 'bounds.json'.")
