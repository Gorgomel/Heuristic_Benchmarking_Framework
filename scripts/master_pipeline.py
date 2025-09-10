# scripts/master_pipeline.py
"""Orquestrador “macro” de campanhas (agendamento sequencial/por lotes)."""

import logging
import subprocess
import sys
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Caminhos relativos à raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTANCE_MANIFEST_PATH = PROJECT_ROOT / "configs" / "instances_to_generate.yaml"
SYNTHETIC_INSTANCES_DIR = PROJECT_ROOT / "data" / "instances" / "synthetic"

GENERATOR_SCRIPT = PROJECT_ROOT / "src" / "generator" / "cli.py"
PIPELINE_SCRIPT = PROJECT_ROOT / "scripts" / "pipeline.py"
EXPERIMENT_PLAN = PROJECT_ROOT / "configs" / "plan_phase_1.yaml"


def generate_instances():
    """Verifica e gera as instâncias sintéticas que faltam."""
    logging.info("--- Fase de Geração de Instâncias ---")

    with open(INSTANCE_MANIFEST_PATH) as f:
        manifest = yaml.safe_load(f)

    epsilon = manifest["epsilon"]
    instances_to_generate = manifest["instances"]

    SYNTHETIC_INSTANCES_DIR.mkdir(parents=True, exist_ok=True)

    for instance_def in instances_to_generate:
        filename = instance_def["filename"]
        params = instance_def["params"]
        output_path = SYNTHETIC_INSTANCES_DIR / filename

        if output_path.exists():
            logging.info(f"Instância '{filename}' já existe. Pulando.")
            continue

        logging.info(f"Gerando instância '{filename}'...")

        command = [
            "poetry",
            "run",
            "python",
            str(GENERATOR_SCRIPT),
            "--nodes",
            str(params["nodes"]),
            "--density",
            str(params["density"]),
            "--cv-vel",
            str(params["cv_vel"]),
            "--output",
            str(output_path),
            "--epsilon",
            str(epsilon),
            "--seed",
            str(params["seed"]),
            "--verbose",
        ]

        try:
            subprocess.run(command, check=True, text=True, capture_output=True)
            logging.info(f"Instância '{filename}' gerada com sucesso.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Falha ao gerar '{filename}'. Erro:\n{e.stderr}")
            # Decide se quer parar ou continuar em caso de falha
            sys.exit(1)  # Para o pipeline se a geração falhar


def run_experiments():
    """Executa a campanha experimental completa usando o pipeline.py."""
    logging.info("--- Fase de Execução dos Experimentos ---")

    command = [
        "poetry",
        "run",
        "python",
        str(PIPELINE_SCRIPT),
        "--plan",
        str(EXPERIMENT_PLAN),
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError:
        logging.error("O pipeline de experimentos falhou. Veja os logs para mais detalhes.")


if __name__ == "__main__":
    logging.info("Iniciando o Pipeline Mestre.")
    generate_instances()
    run_experiments()
    logging.info("Pipeline Mestre concluído.")
