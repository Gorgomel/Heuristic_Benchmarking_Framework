import json
import subprocess
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pytest
from jsonschema import validate

# Adiciona o diretório 'src' ao path do sistema para permitir a importação
sys.path.insert(0, str(Path(__file__).parents[1]))

from src.generator.cli import (
    build_graph,
    generate_velocities,
    save_instance,
)

# --- Carregamento do Schema ---
# Carrega o schema uma vez para ser usado em múltiplos testes
try:
    SCHEMA_PATH = Path(__file__).parents[1] / "specs" / "schema_input.json"
    with open(SCHEMA_PATH, "r") as f:
        SCHEMA = json.load(f)
except FileNotFoundError:
    pytest.fail(
        "Arquivo specs/schema_input.json não encontrado. Crie-o antes de rodar os testes.",
        pytrace=False,
    )


# --- Testes ---


def test_cli_end_to_end(tmp_path):
    """Teste de integração: executa o script via linha de comando e valida a saída."""
    output_file = tmp_path / "cli_instance.json"
    epsilon_value = "50.0"
    cmd = [
        "python",
        "-m",
        "src.generator.cli",
        "--nodes",
        "25",
        "--density",
        "0.2",
        "--cv-vel",
        "0.3",
        "--output",
        str(output_file),
        "--epsilon",
        epsilon_value,  # <-- MUDANÇA: Argumento epsilon adicionado
        "--seed",
        "42",
    ]
    subprocess.run(cmd, check=True)

    assert output_file.exists()
    with open(output_file, "r") as f:
        data = json.load(f)

    validate(instance=data, schema=SCHEMA)
    assert data["epsilon"] == float(
        epsilon_value
    )  # Verifica se o epsilon foi salvo corretamente
    assert len(data["nodes"]) <= 25


def test_save_instance_validates_against_schema(tmp_path):
    """Teste de unidade: verifica se a função save_instance produz um JSON válido."""
    output_file = tmp_path / "unit_test.json"
    rng = np.random.default_rng(101)
    graph = build_graph(rng, 10, 0.5)
    velocities = generate_velocities(rng, graph.number_of_nodes(), 0.2)
    epsilon_value = 50.0

    # MUDANÇA: Passando o argumento 'epsilon' para a função
    save_instance(graph, velocities, output_file, rng, epsilon_value)

    with open(output_file, "r") as f:
        data = json.load(f)
    validate(instance=data, schema=SCHEMA)
    assert "epsilon" in data


def test_cv_accuracy_is_within_tolerance():
    """Verifica se o CV gerado está próximo do alvo com tolerância relativa."""
    rng = np.random.default_rng(202)
    target_cv = 0.4
    velocities = generate_velocities(rng, n=1000, target_cv=target_cv)
    actual_cv = np.std(velocities) / np.mean(velocities)

    assert actual_cv == pytest.approx(target_cv, rel=0.20)


def test_graph_connectivity_and_size():
    """Garante que o grafo retornado é conexo e não perdeu nós em excesso."""
    rng = np.random.default_rng(303)
    num_nodes_req = 100
    graph = build_graph(rng, num_nodes=num_nodes_req, density=0.04)

    assert nx.is_connected(graph)
    assert graph.number_of_nodes() >= num_nodes_req * 0.8


def test_reproducibility_with_seed(tmp_path):
    """Verifica se a mesma seed produz resultados idênticos."""
    epsilon_value = 50.0

    # Execução 1
    rng1 = np.random.default_rng(42)
    g1 = build_graph(rng1, 15, 0.3)
    v1 = generate_velocities(rng1, g1.number_of_nodes(), 0.25)
    out1 = tmp_path / "run1.json"
    save_instance(g1, v1, out1, rng1, epsilon_value)  # <-- MUDANÇA: Epsilon adicionado

    # Execução 2 (mesma seed)
    rng2 = np.random.default_rng(42)
    g2 = build_graph(rng2, 15, 0.3)
    v2 = generate_velocities(rng2, g2.number_of_nodes(), 0.25)
    out2 = tmp_path / "run2.json"
    save_instance(g2, v2, out2, rng2, epsilon_value)  # <-- MUDANÇA: Epsilon adicionado

    # Execução 3 (seed diferente)
    rng3 = np.random.default_rng(43)
    g3 = build_graph(rng3, 15, 0.3)
    v3 = generate_velocities(rng3, g3.number_of_nodes(), 0.25)
    out3 = tmp_path / "run3.json"
    save_instance(g3, v3, out3, rng3, epsilon_value)  # <-- MUDANÇA: Epsilon adicionado

    assert out1.read_text() == out2.read_text()
    assert out1.read_text() != out3.read_text()
