from fabric import Connection
from pathlib import Path

# --- Detalhes da Conexão e do Projeto ---
REMOTE_USER = "brunn"
REMOTE_HOST = "192.168.2.103"
REMOTE_PORT = 2222
REPO_SUBDIR = "Performance_Predictive_Model_Framework"
# ADICIONE O CAMINHO QUE VOCÊ ENCONTROU NO PASSO 1
REMOTE_POETRY_PATH = "/home/brunn/.local/bin/poetry"


def execute_remote_experiment(config_file: str):
    """
    Conecta-se a um host remoto via SSH em uma porta específica,
    atualiza o repositório e executa um experimento nativamente.
    """
    print(
        f"Iniciando orquestração remota em {REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PORT}..."
    )

    # Caminho da chave SSH
    key_path = str(Path.home() / ".ssh" / "id_ed25519")
    connect_kwargs = {"key_filename": key_path}

    # Ação Corretiva: Adicionado o parâmetro 'port' à conexão
    with Connection(
        host=REMOTE_HOST,
        user=REMOTE_USER,
        port=REMOTE_PORT,
        connect_kwargs=connect_kwargs,
    ) as c:
        # Obtemos o diretório HOME do usuário remoto de forma dinâmica
        home_dir = c.run("echo $HOME", hide=True).stdout.strip()
        remote_repo_path = f"{home_dir}/{REPO_SUBDIR}"

        print("--> Conectado. Atualizando repositório remoto via 'git pull'...")
        with c.cd(remote_repo_path):
            result_pull = c.run("git pull", hide=False)
            if result_pull.failed:
                print(
                    f"ERRO: Falha ao executar 'git pull' no host remoto. "
                    f"Código de saída: {result_pull.exited}"
                )
                return

        print("--> Repositório atualizado. Executando experimento nativamente...")

        # AÇÃO CORRETIVA: Usamos o caminho absoluto para o Poetry
        native_command = (
            f"{REMOTE_POETRY_PATH} run python -m src.hpc_framework.cli "
            f"--config {config_file}"
        )

        print(f"--> Executando comando: {native_command}")
        with c.cd(remote_repo_path):
            result_run = c.run(native_command, hide=False, pty=True)

        if result_run.ok:
            print("--> Execução remota concluída com sucesso.")
        else:
            print(
                f"ERRO: A execução remota falhou. "
                f"Código de saída: {result_run.exited}"
            )


if __name__ == "__main__":
    print("Executando teste do orquestrador...")
    execute_remote_experiment(config_file="configs/placeholder_exp.yaml")
