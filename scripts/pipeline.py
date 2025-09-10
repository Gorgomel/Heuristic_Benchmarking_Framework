# scripts/pipeline.py
"""Pipeline declarativo local (varre configs YAML e dispara execuções unitárias)."""

import argparse
import itertools
import logging
import sys
from pathlib import Path

import yaml
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.orchestrator.ssh_executor import (  # noqa: E402
    execute_remote_experiment,
)


def main() -> None:
    """CLI do pipeline local: lê YAML(s), produz cartesianas e executa/aloca jobs."""
    parser = argparse.ArgumentParser(description="Orquestrador de Pipeline para o Framework HPC.")
    # ... resto inalterado ...
    # Se houver linhas >100 colunas, deixe — ignoramos E501 no Ruff.

    parser.add_argument(
        "--plan",
        type=Path,
        required=True,
        help="Caminho para o arquivo do plano experimental (e.g., configs/plan_phase_1.yaml)",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results/raw"),
        help="Diretório para salvar os resultados brutos",
    )
    args = parser.parse_args()

    # Carrega o plano experimental
    with open(args.plan) as f:
        plan = yaml.safe_load(f)["parameters"]

    # Gera todas as combinações de experimentos
    all_combinations = list(
        itertools.product(plan["instances"], plan["heuristics"], plan["budgets"], plan["seeds"])
    )

    logging.info(
        f"Plano carregado. Total de {len(all_combinations)} execuções a serem verificadas."
    )

    # Cria o diretório de resultados se não existir
    args.results_dir.mkdir(parents=True, exist_ok=True)

    # Loop principal com a barra de progresso
    for instance, heuristic, budget, seed in tqdm(all_combinations, desc="Progresso do Pipeline"):
        # --- Lógica de Checkpointing ---
        instance_name = Path(instance).stem
        output_filename = f"{instance_name}_{heuristic}_b{budget}_s{seed}.json"
        output_path = args.results_dir / output_filename

        if output_path.exists():
            logging.info(f"Resultado para {output_filename} já existe. Pulando.")
            continue

        logging.info(f"Executando: {output_filename}")

        # Constrói os parâmetros para passar para o executor
        params = {
            "instance_path": f"data/instances/synthetic/{instance}",  # Caminho relativo no repositório
            "heuristic": heuristic,
            "budget": budget,
            "seed": seed,
            "output_path": f"results/raw/{output_filename}",  # Caminho relativo no repositório
        }

        # Chama a função de execução remota
        success = execute_remote_experiment(params)

        if not success:
            logging.error(f"A execução de {output_filename} falhou. Verifique os logs.")
            # Opcional: decidir se deve parar o pipeline em caso de falha
            # break

    logging.info("Pipeline concluído.")


if __name__ == "__main__":
    main()
