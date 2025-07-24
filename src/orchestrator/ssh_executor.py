# src/orchestrator/ssh_executor.py (versão para execução nativa)

from fabric import Connection
from pathlib import Path

REMOTE_HOST = "brunn@192.168.2.103"
REMOTE_REPO_PATH = "C:/Users/Brunn/Desktop/Performance_Predictive_Model_Framework"  # Confirme se este é o caminho correto no Windows


def execute_remote_experiment(config_file: str):
    print(f"Iniciando orquestração remota em {REMOTE_HOST}...")

    key_path = str(Path.home() / ".ssh" / "id_ed25519")
    connect_kwargs = {"key_filename": key_path}

    with Connection(REMOTE_HOST, connect_kwargs=connect_kwargs) as c:
        print("--> Conectado. Atualizando repositório remoto via 'git pull'...")
        with c.cd(REMOTE_REPO_PATH):
            result_pull = c.run("git pull", hide=False)
            if result_pull.failed:
                print(
                    f"ERRO: Falha ao executar 'git pull' no host remoto. Código de saída: {result_pull.exited}"
                )
                return

        print("--> Repositório atualizado. Executando experimento nativamente...")

        # Comando que será executado nativamente no Windows via Poetry
        native_command = (
            f"poetry run python -m src.hpc_framework.cli " f"--config {config_file}"
        )

        print(f"--> Executando comando: {native_command}")
        # Usamos c.cd() novamente para garantir que o comando seja executado no diretório certo
        with c.cd(REMOTE_REPO_PATH):
            result_run = c.run(native_command, hide=False, pty=True)

        if result_run.ok:
            print("--> Execução remota concluída com sucesso.")
        else:
            print(
                f"ERRO: A execução remota falhou. Código de saída: {result_run.exited}"
            )


if __name__ == "__main__":
    print("Executando teste do orquestrador...")
    execute_remote_experiment(config_file="configs/placeholder_exp.yaml")
