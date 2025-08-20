# src/generator/cli.py
from __future__ import annotations

import argparse
import gzip
import json
import logging
import math
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

import numpy as np
from jsonschema import validate

# =========================
# Parâmetros Globais
# =========================
V_MIN, V_MAX = 8.0, 16.0
POS_MIN, POS_MAX = 0.0, 1000.0

# Gate de modularidade por memória (evita picos de RSS com NetworkX)
MOD_GREEDY_EDGE_LIMIT_ABS = 1_200_000  # teto absoluto de arestas
MOD_GREEDY_EDGE_LIMIT_FRAC = 0.30  # ou 30% de M = n(n-1)/2


def _m_crit(n: int) -> int:
    """Limiar prático para despachar para o modo 'dense-fast'."""
    return int(2 * n * math.log(max(n, 2)))


# =========================
# tqdm fallback (opcional)
# =========================
try:
    from tqdm import tqdm  # type: ignore
except Exception:  # pragma: no cover

    class _TQDMFallback(SimpleNamespace):
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

    tqdm = _TQDMFallback  # type: ignore


# =========================
# Utilidades
# =========================
def _version_tuple(s: str) -> tuple[int, int, int]:
    """'X.Y.Z' -> (X,Y,Z) para comparação semântica robusta."""
    parts = (s.split(".") + ["0", "0"])[:3]
    try:
        return tuple(int(p) for p in parts)  # type: ignore[return-value]
    except ValueError:
        return (0, 0, 0)


def _load_schema() -> Optional[dict]:
    try:
        schema_path = (
            Path(__file__).resolve().parents[2] / "specs" / "schema_input.json"
        )
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning("Arquivo de schema não encontrado. Pulando validação.")
        return None


def _canonicalize_and_sort_edges(edges: np.ndarray) -> np.ndarray:
    """
    Ordena cada par para (min,max) sem efeitos colaterais e ordena linhas.
    Evita self-loops acidentais como (v,v) por operações in-place.
    """
    if edges.size == 0:
        return edges.astype(np.int64)
    edges = edges.astype(np.int64, copy=False)
    u = np.minimum(edges[:, 0], edges[:, 1])
    v = np.maximum(edges[:, 0], edges[:, 1])
    E = np.column_stack((u, v))
    order = np.lexsort((E[:, 1], E[:, 0]))
    return E[order]


def _linear_index_to_edge(indices: np.ndarray, n: int) -> np.ndarray:
    """Converte índices lineares (0..M-1) em pares (i,j), i<j, no triângulo superior de K_n."""
    i = (
        n - 2 - np.floor(np.sqrt(-8 * indices + 4 * n * (n - 1) - 7) / 2 - 0.5)
    ).astype(np.int64)
    j = (indices + i * (i + 1) // 2 - i * n + i + 1).astype(np.int64)
    return np.vstack([i, j]).T


def _edge_to_linear_index(u: np.ndarray, v: np.ndarray, n: int) -> np.ndarray:
    """Inverso de _linear_index_to_edge para i<j, vectorizado."""
    return (u * n + v - u * (u + 1) // 2 - (u + 1)).astype(np.int64)


# =========================
# Algoritmo de Wilson — UST em K_n
# =========================
def random_tree_wilson(rng: np.random.Generator, n: int) -> np.ndarray:
    """
    Uniform Spanning Tree via Algoritmo de Wilson (loop-erased random walks) em K_n.
      - Passo evita auto-laço (não existe aresta (u,u) em K_n).
      - Loop-erasure mantém o nó revisitado (truncamento em cut+1).
      - Caminho é conectado “de trás pra frente” ao primeiro nó já em árvore.
    Retorna (n-1,2) com pares (i,j), i<j, ordenados lexicograficamente.
    """
    if n < 2:
        return np.zeros((0, 2), dtype=np.int64)

    parent = np.full(n, -1, dtype=np.int64)
    in_tree = np.zeros(n, dtype=bool)

    root = int(rng.integers(0, n))
    in_tree[root] = True

    for start in range(n):
        if in_tree[start]:
            continue

        # Caminhada com loop-erasure
        path: list[int] = []
        pos: dict[int, int] = {}
        u = start
        while not in_tree[u]:
            if u in pos:
                cut = pos[u]
                path = path[: cut + 1]  # mantém u revisitado
                pos = {node: i for i, node in enumerate(path)}
            else:
                pos[u] = len(path)
                path.append(u)

            # passo em K_n evitando auto-laço
            r = int(rng.integers(0, n - 1))
            u = r + (r >= u)  # uniforme em {0..n-1}\{u}

        # Conecta caminho à árvore (do fim para o início)
        prev = u  # nó já em árvore
        for v in reversed(path):
            parent[v] = prev
            in_tree[v] = True
            prev = v

    edges = np.array([(i, p) for i, p in enumerate(parent) if p != -1], dtype=np.int64)
    return _canonicalize_and_sort_edges(edges)


# =========================
# Construtor de arestas — Dispatcher “constructive” × “dense-fast”
# =========================
def build_edge_list(
    rng: np.random.Generator, num_nodes: int, target_density: float, verbose: bool
) -> np.ndarray:
    logging.info("Iniciando construção da lista de arestas...")
    tree_edges = random_tree_wilson(rng, num_nodes)

    m_max = num_nodes * (num_nodes - 1) // 2
    m_target = int(target_density * m_max)
    needed = m_target - (num_nodes - 1)
    if needed <= 0:
        return tree_edges

    mode = "dense-fast" if m_target > _m_crit(num_nodes) else "constructive"
    logging.info(f"Árvore criada; adicionando {needed:,} arestas... (mode={mode})")

    # Máscara global — marca as da árvore
    mask = np.ones(m_max, dtype=bool)
    u, v = tree_edges.T
    mask[_edge_to_linear_index(u, v, num_nodes)] = False

    new_edges: list[np.ndarray] = []
    stall = 0
    acceptance_last = 0.0

    if mode == "constructive":
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
                        factor = min(2.0, factor * 1.2)
                    continue

                unique = np.unique(valid)
                use = unique[:needed]
                if use.size:
                    mask[use] = False
                    new_edges.append(_linear_index_to_edge(use, num_nodes))
                    pbar.update(int(use.size))
                    acceptance_last = float(valid.size) / float(
                        batch_size
                    )  # taxa bruta do pool
                    if verbose and pbar.n == use.size:
                        logging.info(
                            f"pool={batch_size:,}, aceitação={100*acceptance_last:.1f}% (faltam={needed:,})"
                        )
                    needed -= int(use.size)
                    stall = 0
    else:
        factor = 3.8  # agressivo
        with tqdm(
            total=needed,
            desc="Adicionando arestas (dense-fast)",
            unit="aresta",
            disable=(not verbose) or (not sys.stderr.isatty()),
        ) as pbar:
            while needed > 0:
                batch_size = max(200_000, int(needed * factor))
                cand = rng.integers(0, m_max, batch_size, dtype=np.int64)
                valid = cand[mask[cand]]
                if valid.size == 0:
                    stall += 1
                    if stall >= 2:
                        factor = min(6.0, factor * 1.2)
                    continue

                unique = np.unique(valid)
                use = unique[:needed]
                if use.size:
                    mask[use] = False
                    new_edges.append(_linear_index_to_edge(use, num_nodes))
                    pbar.update(int(use.size))
                    acceptance_last = float(valid.size) / float(batch_size)
                    if verbose and pbar.n == use.size:
                        logging.info(
                            f"pool={batch_size:,}, aceitação={100*acceptance_last:.1f}% (faltam={needed:,})"
                        )
                    needed -= int(use.size)
                    stall = 0

    edges = np.vstack([tree_edges] + new_edges)
    edges = _canonicalize_and_sort_edges(edges)

    # Telemetria leve (consumida no save)
    global _TELEMETRY  # noqa: PLW0603
    _TELEMETRY = SimpleNamespace(
        tree_method="wilson",
        density_mode=mode,
        acceptance_last=acceptance_last,
        # vel_sampler/cv_capped são preenchidos em generate_velocities
    )
    return edges


# =========================
# Samplers de velocidades: Beta 4p (CV baixo) + Mistura simétrica (CV alto)
# =========================
def _beta_4p_from_mean_cv(mean_target: float, cv_target: float) -> tuple[float, float]:
    """Converte (média, CV) em [V_MIN,V_MAX] para (α,β) de uma Beta em [0,1]."""
    a, b = V_MIN, V_MAX
    width = b - a
    mu_t = float(mean_target)
    sigma_t = float(cv_target * mu_t)

    mu_x = (mu_t - a) / width
    var_x = (sigma_t / width) ** 2

    eps = 1e-12
    max_var = max(mu_x * (1.0 - mu_x) - eps, 1e-16)
    if var_x >= max_var:
        logging.warning(
            "Beta4p inviável p/ mean=%.4f, cv=%.4f; ajustando var %.3e -> %.3e.",
            mu_t,
            cv_target,
            var_x,
            0.999 * max_var,
        )
        var_x = 0.999 * max_var

    nu = (mu_x * (1.0 - mu_x)) / var_x - 1.0
    alpha = mu_x * nu
    beta = (1.0 - mu_x) * nu
    return float(alpha), float(beta)


def generate_velocities(
    rng: np.random.Generator, n: int, target_cv: float
) -> np.ndarray:
    """
    Gera 'n' velocidades em [V_MIN,V_MAX] com média no centro e CV alvo.
      - CV ≤ 0.29: Beta 4-parâmetros (moment matching), reescala e clip; realinha média uma vez.
      - CV > 0.29: mistura simétrica (50/50) nos extremos + ruído leve + correção de escala; média recentrada.
    Audita |CV_emp - CV_alvo| > 0.02 (n ≥ 100). Clampa CV ao teto teórico com média no centro (1/3).
    """
    target_mean = (V_MAX + V_MIN) / 2.0
    cv_max_centered = (V_MAX - V_MIN) / (V_MAX + V_MIN)  # 1/3

    cv_capped = False
    vel_sampler = (
        "beta4p"  # default robusto (também usado no caso quase-determinístico)
    )

    if target_cv > cv_max_centered:
        logging.warning(
            "CV alvo %.4f excede limite teórico com média no centro (%.4f). Usando %.4f.",
            target_cv,
            cv_max_centered,
            cv_max_centered,
        )
        target_cv = cv_max_centered
        cv_capped = True

    if target_cv < 1e-6:
        v = np.full(n, target_mean, dtype=float)
    elif target_cv <= 0.29:
        alpha, beta = _beta_4p_from_mean_cv(target_mean, target_cv)
        x = rng.beta(alpha, beta, size=n)  # [0,1]
        v = V_MIN + (V_MAX - V_MIN) * x  # [V_MIN, V_MAX]
        v += target_mean - v.mean()  # realinha média uma vez
        v = np.clip(v, V_MIN, V_MAX)
        vel_sampler = "beta4p"
    else:
        half = n // 2
        v = np.empty(n, dtype=float)
        v[:half] = V_MIN
        v[half:] = V_MAX
        rng.shuffle(v)

        noise_std = 0.005 * (V_MAX - V_MIN)
        v = np.clip(v + rng.normal(0, noise_std, n), V_MIN, V_MAX)

        target_std = target_cv * target_mean
        mean_emp, std_emp = v.mean(), v.std()
        if std_emp > 1e-12:
            v = mean_emp + (target_std / std_emp) * (v - mean_emp)
        v += target_mean - v.mean()
        v = np.clip(v, V_MIN, V_MAX)
        vel_sampler = "mixture"

    # Auditoria (tolerância 0.02)
    if n >= 100:
        cv_emp = float(v.std() / (v.mean() + 1e-12))
        if abs(cv_emp - target_cv) > 0.02:
            logging.warning(
                "CV fora da tolerância: emp=%.4f vs alvo=%.4f (|Δ|=%.4f) [n=%d]",
                cv_emp,
                target_cv,
                abs(cv_emp - target_cv),
                n,
            )

    ns = globals().get("_TELEMETRY")
    if not isinstance(ns, SimpleNamespace):
        ns = SimpleNamespace()
    ns.vel_sampler = vel_sampler
    ns.cv_capped = cv_capped
    global _TELEMETRY
    _TELEMETRY = ns
    return v


# =========================
# Modularidade (gate por memória)
# =========================
def _compute_modularity_greedy_if_small(
    edges: np.ndarray, n_nodes: int
) -> Optional[float]:
    """
    Calcula modularidade via greedy (CNM) **apenas** se o grafo for pequeno o bastante
    para não estourar memória com NetworkX — limite efetivo: min(ABS, FRAC·M).
    """
    m = int(edges.shape[0])
    M = n_nodes * (n_nodes - 1) // 2
    dynamic_limit = min(MOD_GREEDY_EDGE_LIMIT_ABS, int(MOD_GREEDY_EDGE_LIMIT_FRAC * M))

    if m > dynamic_limit:
        logging.warning(
            "Grafo grande (>%s arestas); modularidade pulada.", f"{dynamic_limit:,}"
        )
        return None

    try:
        import networkx as nx  # lazy import
    except ImportError:
        logging.warning("NetworkX ausente; modularidade pulada.")
        return None

    if _version_tuple(nx.__version__) < (2, 6, 0):
        logging.warning("NetworkX < 2.6; modularidade pulada.")
        return None

    G = nx.Graph()
    G.add_nodes_from(range(n_nodes))
    G.add_edges_from(edges.tolist())
    comms = nx.community.greedy_modularity_communities(G)
    return float(nx.community.modularity(G, comms))


# =========================
# Save helpers e wrappers p/ testes
# =========================
def _save_instance_core(
    edges: np.ndarray,
    velocities: np.ndarray,
    output_path: Path,
    rng: np.random.Generator,
    schema: dict | None,
    params: dict,
) -> None:
    """Serializa JSON (respeita a extensão informada: .json ou .json.gz)."""
    n = int(velocities.size)
    modularity = _compute_modularity_greedy_if_small(edges, n)

    # Meta (telemetria leve) — não polui instance_metrics
    meta = {}
    if isinstance(globals().get("_TELEMETRY"), SimpleNamespace):
        t = globals()["_TELEMETRY"].__dict__
        meta = {
            "tree_method": t.get("tree_method"),
            "density_mode": t.get("density_mode"),
            "vel_sampler": t.get("vel_sampler"),
            "acceptance_last": float(t.get("acceptance_last", 0.0)),
            "cv_capped": bool(t.get("cv_capped", False)),
        }

    instance = {
        "schema_version": "1.1",
        "epsilon": params["epsilon"],
        "instance_metrics": {
            "nodes_requested": params["nodes_requested"],
            "nodes_final": n,
            "density_requested": params["density_requested"],
            "density_final": float(
                edges.shape[0] / (n * (n - 1) / 2) if n > 1 else 0.0
            ),
            "cv_vel_requested": params["cv_vel_requested"],
            "cv_vel_final": float(velocities.std() / (velocities.mean() + 1e-12)),
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

    if schema is not None:
        validate(instance=instance, schema=schema)
        logging.info("Validação JSONSchema concluída.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if str(output_path).endswith(".gz"):
        with gzip.open(str(output_path), "wt", encoding="utf-8") as f:
            json.dump(instance, f, indent=2)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(instance, f, indent=2)
    logging.info(f"Instância salva em {output_path}")


def build_graph(rng: np.random.Generator, num_nodes: int, density: float) -> Any:
    """Shim p/ testes: materializa um nx.Graph **apenas** para n pequenos (uso em tests/)."""
    edges = build_edge_list(rng, num_nodes, density, verbose=False)
    try:
        import networkx as nx  # lazy
    except ImportError:  # pragma: no cover
        raise RuntimeError("NetworkX não instalado para o shim de testes.")
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    G.add_edges_from(edges.tolist())
    return G


def save_instance(
    graph: Any,
    velocities: np.ndarray,
    output_path: Path,
    rng: np.random.Generator,
    epsilon: float,
) -> None:
    """
    Shim p/ testes: extrai arestas do grafo e delega para o core.
    'cv_vel_requested' é preenchido com o CV observado (semântica do teste).
    """
    n = graph.number_of_nodes()
    edges = np.array(list(graph.edges()), dtype=np.int64)
    edges = _canonicalize_and_sort_edges(edges)

    schema = _load_schema()
    params = {
        "nodes_requested": n,
        "density_requested": float(
            (2 * graph.number_of_edges()) / (n * (n - 1)) if n > 1 else 0.0
        ),
        "cv_vel_requested": float(velocities.std() / (velocities.mean() + 1e-12)),
        "seed": None,
        "epsilon": float(epsilon),
    }
    _save_instance_core(edges, velocities, output_path, rng, schema, params)


# =========================
# CLI
# =========================
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Gerador de Instâncias HPC (v6.1.0)\n"
            "Notas:\n"
            " - Árvore base por Wilson (UST) + complemento via índices.\n"
            " - CV teórico máximo com média no centro é (Vmax-Vmin)/(Vmax+Vmin) = 1/3 ≈ 0.333.\n"
            " - Modularidade greedy só em grafos pequenos (gate por memória)."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--nodes", type=int, required=True)
    parser.add_argument("--density", type=float, required=True)
    parser.add_argument(
        "--cv-vel",
        type=float,
        required=True,
        help="Coeficiente de variação alvo (0..1). Máx efetivo ≈ 0.333 com média no centro.",
    )
    parser.add_argument("--epsilon", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # Fail-fast
    assert args.nodes >= 2, "--nodes deve ser >= 2"
    assert 0.0 < args.density < 1.0, "--density deve estar em (0,1)"
    assert 0.0 <= args.cv_vel <= 1.0, "--cv-vel deve estar em [0,1]"

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
