# src/orchestrator/ssh_executor.py
import logging
from fabric import Connection
from pathlib import Path

# --- Detalhes da Conexão e do Projeto ---
REMOTE_USER = "brunn"
REMOTE_HOST = "192.168.2.103"
REMOTE_PORT = 2222
REMOTE_REPO_PATH = "/home/brunn/MPP"  # Caminho Linux dentro do WSL1
REMOTE_POETRY_PATH = "/home/brunn/.local/bin/poetry"


def execute_remote_experiment(params: dict) -> bool:
    """
    Executa um ÚNICO experimento remotamente. Retorna True em sucesso, False em falha.
    """
    key_path = str(Path.home() / ".ssh" / "id_ed25519")
    connect_kwargs = {"key_filename": key_path}

    # Constrói o comando CLI a partir dos parâmetros
    command_cli = (
        f"python -m src.heuristics.cli "
        f"--instance {params['instance_path']} "
        f"--heuristic {params['heuristic']} "
        f"--budget {params['budget']} "
        f"--output {params['output_path']} "
        f"--seed {params['seed']}"
    )

    # Envolve o comando CLI com o poetry
    full_command = f"{REMOTE_POETRY_PATH} run {command_cli}"

    try:
        with Connection(
            host=REMOTE_HOST,
            user=REMOTE_USER,
            port=REMOTE_PORT,
            connect_kwargs=connect_kwargs,
        ) as c:
            logging.info("--> Conectado. Atualizando repositório...")
            with c.cd(REMOTE_REPO_PATH):
                # O git pull pode ser feito apenas uma vez no início do pipeline,
                # mas por segurança, deixamos aqui.
                c.run("git pull", hide=True)

                logging.info(f"--> Executando comando: {full_command}")
                result = c.run(full_command, hide=False, pty=True)

        return result.ok

    except Exception as e:
        logging.error(f"Falha na conexão ou execução SSH: {e}")
        return False
