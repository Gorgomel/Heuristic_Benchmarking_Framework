# src/orchestrator/ssh_executor.py

from fabric import Connection

# --- Detalhes da Conexão e do Projeto ---
# Estes valores devem ser movidos para um arquivo de configuração no futuro.
REMOTE_HOST = "brunn@192.168.2.103"
REMOTE_REPO_PATH = "C:/Users/Brunn/dev/MPP-Framework"  # O caminho no Windows
DOCKER_IMAGE = "mpp-framework:dev"


def execute_remote_experiment(config_file: str):
    """
    Conecta-se a um host remoto, atualiza o repositório e executa um
    experimento dentro de um container Docker.

    Args:
        config_file: O caminho relativo do arquivo de configuração do experimento.
                     Ex: 'configs/exp_001.yaml'
    """
    print(f"Iniciando orquestração remota em {REMOTE_HOST}...")

    # A sintaxe 'with' garante que a conexão SSH seja fechada corretamente.
    with Connection(REMOTE_HOST) as c:
        print("--> Conectado. Atualizando repositório remoto via 'git pull'...")
        # O with c.cd(...) garante que os comandos rodem no diretório correto.
        with c.cd(REMOTE_REPO_PATH):
            result = c.run("git pull", hide=False)
            if result.failed:
                print("ERRO: Falha ao executar 'git pull' no host remoto.")
                return

        print(f"--> Repositório atualizado. Executando o container {DOCKER_IMAGE}...")

        # Constrói o comando que será executado dentro do container
        # Nota: O caminho do config_file precisa ser acessível dentro do container.
        # Por enquanto, vamos assumir que ele está no repositório.
        command_inside_container = (
            f"poetry run python -m src.hpc_framework.cli " f"--config {config_file}"
        )

        # Constrói o comando docker run completo
        docker_command = f"docker run --rm {DOCKER_IMAGE} {command_inside_container}"

        print(f"--> Executando comando: {docker_command}")
        result = c.run(docker_command, hide=False, pty=True)

        if result.ok:
            print("--> Execução remota concluída com sucesso.")
        else:
            print("ERRO: A execução remota falhou.")


if __name__ == "__main__":
    # Um exemplo de como chamar a função para teste.
    # Precisamos criar um arquivo de config placeholder para este teste.
    # Por enquanto, vamos apenas chamar a função com um nome de arquivo fictício.
    print("Executando teste do orquestrador...")
    # ATENÇÃO: Este comando vai falhar se o arquivo de config não existir no repo.
    # O objetivo agora é testar a conexão e a execução dos comandos.
    execute_remote_experiment(config_file="configs/placeholder_exp.yaml")
