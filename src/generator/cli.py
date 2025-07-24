import argparse
import json
import logging
from pathlib import Path

import networkx as nx
import numpy as np
from jsonschema import ValidationError, validate

# --- Parâmetros Globais do Protocolo ---
V_MIN, V_MAX = 8.0, 16.0
POS_MIN, POS_MAX = 0.0, 1000.0
MAX_CV_ITERATIONS = 20
CV_TOLERANCE = 0.01


def _load_schema():
    """Carrega o schema de validação a partir do diretório 'specs'."""
    try:
        schema_path = Path(__file__).parents[2] / "specs" / "schema_input.json"
        with open(schema_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning("Arquivo de schema não encontrado. Pulando validação.")
        return None


def generate_velocities(
    rng: np.random.Generator, n: int, target_cv: float
) -> np.ndarray:
    """
    Gera um array de 'n' velocidades, iterativamente ajustando a dispersão
    para se aproximar de um Coeficiente de Variação (CV) alvo.
    """
    mean_vel = (V_MAX + V_MIN) / 2
    scale = target_cv * mean_vel

    for _ in range(MAX_CV_ITERATIONS):
        velocities = rng.normal(loc=mean_vel, scale=scale, size=n)
        velocities = np.clip(velocities, V_MIN, V_MAX)

        current_cv = velocities.std() / (velocities.mean() + 1e-9)

        if abs(current_cv - target_cv) < CV_TOLERANCE:
            break

        scale *= target_cv / (current_cv + 1e-9)
    else:
        logging.warning(
            f"CV de velocidade não convergiu para o alvo {target_cv:.2f}. "
            f"Resultado final: {current_cv:.2f}"
        )
    return velocities


def build_graph(rng: np.random.Generator, num_nodes: int, density: float) -> nx.Graph:
    """
    Constrói um grafo aleatório e garante que ele seja conexo,
    retornando seu maior componente gigante caso não seja.
    """
    g = nx.gnp_random_graph(n=num_nodes, p=density, seed=rng)
    if not nx.is_connected(g):
        logging.warning(
            f"Grafo inicial com {num_nodes} nós e densidade {density} não é conexo. "
            "Extraindo o componente gigante."
        )
        giant_component_nodes = max(nx.connected_components(g), key=len)
        g = g.subgraph(giant_component_nodes).copy()
        g = nx.convert_node_labels_to_integers(g)
    return g


def save_instance(
    graph: nx.Graph,
    velocities: np.ndarray,
    output_path: Path,
    rng: np.random.Generator,
    epsilon: float,
):
    """
    Formata a instância no JSON contratado, valida contra o schema e salva em disco.
    """
    data_to_save = {
        "epsilon": epsilon,  # <-- MUDANÇA: Epsilon adicionado ao output
        "nodes": [
            {
                "id": int(node),
                "velocity": float(velocities[i]),
                "pos": rng.uniform(POS_MIN, POS_MAX, 2).tolist(),
            }
            for i, node in enumerate(graph.nodes())
        ],
        "edges": [[int(u), int(v)] for u, v in graph.edges()],
    }

    schema = _load_schema()
    if schema:
        try:
            validate(instance=data_to_save, schema=schema)
        except ValidationError as e:
            logging.error(
                f"Instância gerada falhou na validação do schema: {e.message}"
            )
            raise

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data_to_save, f, indent=2)


def main():
    """Ponto de entrada principal para a interface de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Gerador de Instâncias para o HPC Framework",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--nodes", type=int, required=True, help="Número de nós (veículos)"
    )
    parser.add_argument(
        "--density",
        type=float,
        required=True,
        help="Densidade do grafo (probabilidade de aresta)",
    )
    parser.add_argument(
        "--cv-vel",
        type=float,
        required=True,
        help="Coeficiente de Variação alvo para as velocidades",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Caminho para o arquivo de saída JSON",
    )
    parser.add_argument(
        "--epsilon",
        type=float,
        default=50.0,
        help="Raio de comunicação/visibilidade para a construção do grafo ε-ball",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed para o gerador de números aleatórios para reprodutibilidade",
    )
    parser.add_argument("--verbose", action="store_true", help="Ativa logs detalhados")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    logging.info(f"Iniciando geração com seed={args.seed}")

    rng = np.random.default_rng(args.seed)

    graph = build_graph(rng, args.nodes, args.density)

    actual_nodes = graph.number_of_nodes()
    velocities = generate_velocities(rng, actual_nodes, args.cv_vel)

    save_instance(
        graph, velocities, args.output, rng, args.epsilon
    )  # <-- MUDANÇA: Passando epsilon

    logging.info(f"Instância com {actual_nodes} nós salva com sucesso em {args.output}")


if __name__ == "__main__":
    main()
