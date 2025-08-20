import argparse
import gzip
import json
import logging
import sys
from pathlib import Path
from types import SimpleNamespace
import heapq
import numpy as np
from jsonschema import validate

try:
    from tqdm import tqdm
except ImportError:

    class TQDMFallback(SimpleNamespace):
        def __init__(self, iterable=None, **kwargs):
            self.iterable = iterable or []

        def __iter__(self):
            return iter(self.iterable)

        def update(self, *a, **kw):
            pass

        def close(self, *a, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

    tqdm = TQDMFallback

V_MIN, V_MAX = 8.0, 16.0
POS_MIN, POS_MAX = 0.0, 1000.0


def _load_schema():
    try:
        schema_path = (
            Path(__file__).resolve().parents[2] / "specs" / "schema_input.json"
        )
        with open(schema_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning("Arquivo de schema não encontrado. Pulando validação.")
        return None


def generate_velocities(
    rng: np.random.Generator, n: int, target_cv: float
) -> np.ndarray:
    target_mean = (V_MAX + V_MIN) / 2
    if target_cv < 1e-6:
        return np.full(n, target_mean)

    if target_cv <= 0.29:
        target_std = target_cv * target_mean
        v = rng.normal(loc=target_mean, scale=target_std, size=n)
        v = np.clip(v, V_MIN, V_MAX)
        mean_clipped, std_clipped = v.mean(), v.std()
        if std_clipped > 1e-6:
            v = mean_clipped + (target_std / std_clipped) * (v - mean_clipped)
        v += target_mean - v.mean()
        return np.clip(v, V_MIN, V_MAX)
    else:
        # Método bimodal calibrado
        pi = _get_bimodal_pi_for_cv(target_cv)
        pi_discrete = round(pi * n) / n
        n_high = int(n * pi_discrete)
        n_low = n - n_high
        v_bimodal = np.concatenate([np.full(n_low, V_MIN), np.full(n_high, V_MAX)])
        rng.shuffle(v_bimodal)
        noise_std = 0.005 * (V_MAX - V_MIN)
        v_bimodal = np.clip(v_bimodal + rng.normal(0, noise_std, n), V_MIN, V_MAX)
        target_mean = pi_discrete * V_MAX + (1 - pi_discrete) * V_MIN
        target_std = np.sqrt(
            pi_discrete * (V_MAX - target_mean) ** 2
            + (1 - pi_discrete) * (V_MIN - target_mean) ** 2
        )
        mean_final, std_final = v_bimodal.mean(), v_bimodal.std()
        if std_final > 1e-6:
            final = mean_final + (target_std / std_final) * (v_bimodal - mean_final)
        else:
            final = v_bimodal
        final = np.clip(final, V_MIN, V_MAX)
        if logging.getLogger().isEnabledFor(logging.INFO):
            logging.info(
                "CV final (bimodal): %.3f (alvo=%.3f)",
                final.std() / (final.mean() + 1e-9),
                target_cv,
            )

        # if abs(final_cv - target_cv) > 0.02:
        #   return generate_velocities(rng, n, 0.28)
        return final


def _get_bimodal_pi_for_cv(target_cv: float, tolerance=1e-4) -> float:
    low, high = 0.0, 0.5
    for _ in range(30):
        mid = (low + high) / 2
        if _cv_bimodal(mid) < target_cv:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def _cv_bimodal(pi: float) -> float:
    mu = pi * V_MAX + (1 - pi) * V_MIN
    var = pi * (V_MAX - mu) ** 2 + (1 - pi) * (V_MIN - mu) ** 2
    return np.sqrt(var) / mu


def _prufer_to_edges(prufer: np.ndarray) -> np.ndarray:
    n = prufer.size + 2
    degree = np.ones(n, dtype=np.int64)
    nodes, counts = np.unique(prufer, return_counts=True)
    degree[nodes] += counts

    leaves = [i for i, d in enumerate(degree) if d == 1]
    heapq.heapify(leaves)

    edges = np.zeros((n - 1, 2), dtype=np.int64)
    for i, v in enumerate(prufer):
        u = heapq.heappop(leaves)
        edges[i] = [u, v]
        degree[v] -= 1
        if degree[v] == 1:
            heapq.heappush(leaves, v)
    # última aresta
    edges[-1] = [heapq.heappop(leaves), heapq.heappop(leaves)]
    return edges


def _linear_index_to_edge(indices: np.ndarray, n: int) -> np.ndarray:
    i = (
        n - 2 - np.floor(np.sqrt(-8 * indices + 4 * n * (n - 1) - 7) / 2 - 0.5)
    ).astype(np.int64)
    j = (indices + i * (i + 1) // 2 - i * n + i + 1).astype(np.int64)
    return np.vstack([i, j]).T


def random_tree_wilson(rng: np.random.Generator, n: int) -> np.ndarray:
    """
    Uniform Spanning Tree em K_n via Algoritmo de Wilson.
    Retorna array (n-1, 2) de arestas, cada par como (u,v) com u < v.
    Determinístico dado o rng.
    """
    if n <= 1:
        return np.empty((0, 2), dtype=np.int64)

    in_tree = np.zeros(n, dtype=bool)
    parent = np.full(n, -1, dtype=np.int64)

    # raiz aleatória
    root = int(rng.integers(0, n))
    in_tree[root] = True

    for start in range(n):
        if in_tree[start]:
            continue

        curr = start
        path: list[int] = []
        pos: dict[int, int] = {}

        # random walk com loop-erasure
        while not in_tree[curr]:
            if curr in pos:
                k = pos[curr]
                for node in path[k + 1 :]:
                    pos.pop(node, None)
                path = path[: k + 1]
            else:
                pos[curr] = len(path)
                path.append(curr)

            r = int(rng.integers(0, n - 1))
            nxt = r + (r >= curr)  # evita auto-laço
            curr = nxt

        # conecta caminho à árvore (curr já está na árvore)
        prev = curr
        for v in reversed(path):
            parent[v] = prev
            in_tree[v] = True
            prev = v

    # materializa arestas (min,max) e ordena (determinismo)
    uu, vv = [], []
    for i, p in enumerate(parent):
        if p != -1:
            a, b = (i, p) if i < p else (p, i)
            uu.append(a)
            vv.append(b)
    edges = np.vstack([np.array(uu, dtype=np.int64), np.array(vv, dtype=np.int64)]).T
    if edges.size:
        edges = edges[np.lexsort((edges[:, 1], edges[:, 0]))]
    return edges


def build_edge_list(
    rng: np.random.Generator, num_nodes: int, target_density: float, verbose: bool
) -> np.ndarray:
    logging.info("Iniciando construção da lista de arestas...")

    tree_edges = random_tree_wilson(rng, num_nodes)
    m_max = num_nodes * (num_nodes - 1) // 2
    m_target = int(target_density * m_max)
    needed = m_target - (num_nodes - 1)

    if needed <= 0:
        tree_edges = np.sort(tree_edges, axis=1)
        tree_edges = tree_edges[np.lexsort((tree_edges[:, 1], tree_edges[:, 0]))]
        return tree_edges

    logging.info(f"Árvore criada; adicionando {needed} arestas de densidade...")

    mask = np.ones(m_max, dtype=bool)

    u, v = tree_edges.T
    idx = u * num_nodes + v - u * (u + 1) // 2 - (u + 1)
    idx = idx.astype(np.int64)
    mask[idx] = False

    new_edges = []
    stall = 0
    factor = 1.3

    with tqdm(
        total=needed,
        desc="Adicionando arestas",
        unit="aresta",
        disable=(not verbose) or (not sys.stderr.isatty()),
    ) as pbar:
        while needed > 0:
            batch_size = max(20_000, int(needed * factor))
            cand = rng.integers(0, m_max, batch_size, dtype=np.int64)

            valid = cand[mask[cand]]
            if valid.size == 0:
                stall += 1
                if stall >= 3:
                    factor = max(factor, 1.8)
                continue

            unique = np.unique(valid)
            mask[unique] = False

            use = unique[:needed]
            if use.size:
                new_edges.append(_linear_index_to_edge(use, num_nodes))
                pbar.update(int(use.size))
                needed -= int(use.size)
                stall = 0

    edges = np.vstack([tree_edges] + new_edges)
    edges = np.sort(edges, axis=1)
    edges = edges[np.lexsort((edges[:, 1], edges[:, 0]))]

    return edges


def build_graph(
    rng: np.random.Generator,
    num_nodes: int,
    density: float = None,
    target_density: float = None,
):
    td = target_density if target_density is not None else density
    if td is None:
        raise TypeError("Informe 'density' (ou 'target_density').")
    edges = build_edge_list(rng, num_nodes, td, verbose=False)

    # Limiar de segurança: muito acima do que os testes usam (n=10,15,100)
    if not (num_nodes <= 2_000 and len(edges) <= 200_000):
        raise RuntimeError(
            "build_graph() é apenas para instâncias pequenas (uso em testes). "
            "Use build_edge_list() no fluxo real (JSON-first)."
        )

    import networkx as nx  # lazy-import

    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    G.add_edges_from(edges.tolist())
    return G


def _save_instance_core(
    edges: np.ndarray,
    velocities: np.ndarray,
    output_path: Path,
    rng: np.random.Generator,
    schema: dict | None,
    params: dict,
):
    # Canonizar arestas para determinismo (min,max) + ordenação lexicográfica
    if not isinstance(edges, np.ndarray):
        edges = np.asarray(edges, dtype=np.int64)
    if edges.size:
        edges = edges.astype(np.int64, copy=False)
        # cada par como (min, max)
        edges = np.sort(edges, axis=1)
        # ordenação global
        order = np.lexsort((edges[:, 1], edges[:, 0]))
        edges = edges[order]

    modularity = None
    try:
        import networkx as nx  # Lazy-import apenas para métricas

        assert nx.__version__ >= "2.6"
        if len(edges) <= 2_000_000:
            G = nx.Graph()
            G.add_nodes_from(range(len(velocities)))
            G.add_edges_from(edges.tolist())
            comms = nx.community.greedy_modularity_communities(G)
            modularity = nx.community.modularity(G, comms)
    except (ImportError, AssertionError):
        logging.warning("NetworkX ausente ou versão <2.6; modularidade pulada.")

    n = len(velocities)
    instance = {
        "schema_version": "1.1",
        "epsilon": params["epsilon"],
        "instance_metrics": {
            "nodes_requested": params["nodes_requested"],
            "nodes_final": n,
            "density_requested": params["density_requested"],
            "density_final": len(edges) / (n * (n - 1) / 2) if n > 1 else 0,
            "cv_vel_requested": params["cv_vel_requested"],
            "cv_vel_final": float(velocities.std() / (velocities.mean() + 1e-9)),
            "modularity": modularity,
            "seed": params["seed"],
        },
        "nodes": [
            {
                "id": i,
                "velocity": float(velocities[i]),
                "pos": rng.uniform(POS_MIN, POS_MAX, 2).tolist(),
            }
            for i in range(n)
        ],
        "edges": [[int(u), int(v)] for u, v in edges],
    }

    # Validar contra schema (agora modularity pode ser null por v1.1)
    if schema and len(edges) <= 5_000_000:
        validate(instance=instance, schema=schema)
        logging.info("Validação JSONSchema concluída.")

    # Respeitar extensão pedida
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_path_str = str(output_path)
    if out_path_str.endswith(".gz"):
        # grava gzip texto
        with gzip.open(out_path_str, "wt", encoding="utf-8") as f:
            json.dump(instance, f, indent=2)
    else:
        # grava JSON plano no caminho EXATO (sem forçar .gz)
        with open(out_path_str, "w", encoding="utf-8") as f:
            json.dump(instance, f, indent=2)

    logging.info(f"Instância salva em {output_path}")


def save_instance(
    graph,  # networkx.Graph esperado pelos testes
    velocities: np.ndarray,
    output_path: Path,
    rng: np.random.Generator,
    epsilon: float,
):
    import networkx as nx  # type: ignore

    if not isinstance(graph, nx.Graph):
        raise TypeError(
            "save_instance(graph, ...) espera um networkx.Graph no primeiro argumento."
        )

    n = graph.number_of_nodes()
    m = graph.number_of_edges()

    # Extrair arestas em ndarray int64
    edges = np.asarray(list(graph.edges()), dtype=np.int64)
    if edges.size:
        edges = np.sort(edges, axis=1)
        order = np.lexsort((edges[:, 1], edges[:, 0]))
        edges = edges[order]
    else:
        edges = edges.reshape(0, 2)

    # Construir params mínimos para métricas/contrato
    m_max = n * (n - 1) / 2 if n > 1 else 1
    density_req = m / m_max
    cv_req = (
        float(velocities.std() / (velocities.mean() + 1e-9)) if len(velocities) else 0.0
    )
    params = {
        "nodes_requested": n,
        "density_requested": density_req,
        "cv_vel_requested": cv_req,
        "seed": None,
        "epsilon": float(epsilon),
    }

    schema = _load_schema()
    return _save_instance_core(edges, velocities, output_path, rng, schema, params)


def main():
    parser = argparse.ArgumentParser(description="Gerador de Instâncias HPC (v5.3)")
    parser.add_argument("--nodes", type=int, required=True)
    parser.add_argument("--density", type=float, required=True)
    parser.add_argument("--cv-vel", type=float, required=True)
    parser.add_argument("--epsilon", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="[%(levelname)s] %(message)s",
    )

    rng = np.random.default_rng(args.seed)
    edges = build_edge_list(rng, args.nodes, args.density, args.verbose)
    velocities = generate_velocities(rng, args.nodes, args.cv_vel)

    params = {
        "nodes_requested": args.nodes,
        "density_requested": args.density,
        "cv_vel_requested": args.cv_vel,
        "seed": args.seed,
        "epsilon": args.epsilon,
    }
    schema = _load_schema()
    _save_instance_core(edges, velocities, args.output, rng, schema, params)


if __name__ == "__main__":
    main()
