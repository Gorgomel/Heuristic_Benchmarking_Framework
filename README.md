````markdown
# MPP-Framework: Framework de Caracterização de Heurísticas

Framework para a execução de experimentos e caracterização de performance multi-objetivo de meta-heurísticas aplicadas ao problema de clusterização de veículos autônomos.

Este projeto visa implementar o protocolo de pesquisa `proto_v3.1.1` para validar a tese de que o desempenho de diferentes algoritmos é uma função das características da instância do problema.

## 🚀 Estrutura do Repositório

- **/docs**: Documentação formal, incluindo o protocolo da pesquisa e relatórios técnicos.
- **/specs**: Os "contratos" de dados do projeto, como JSON Schemas e limites de normalização.
- **/src**: Código-fonte principal do framework, dividido em módulos (`generator`, `heuristics`, `orchestrator`, etc.).
- **/tests**: Suíte de testes automatizados (`pytest`) que garantem a corretude do código em `src/`.
- **/data**: Dados de entrada para os experimentos. As instâncias em `data/instances/` são versionadas via Git LFS.
- **/notebooks**: Jupyter Notebooks para análise exploratória e visualização dos resultados.
- **/scripts**: Scripts utilitários para automação de tarefas (execução remota, agregação de resultados).

## 🛠️ Guia de Instalação e Setup

Este projeto utiliza [Poetry](https://python-poetry.org/) para gerenciamento de dependências e ambiente.

**Requisitos:**
- Python 3.11+
- Git e Git LFS
- Poetry

**Passos para Setup (Ambiente de Desenvolvimento - WSL2):**

1.  **Clonar o repositório:**
    ```bash
    git clone https://github.com/Gorgomel/Performance_Predictive_Model_Framework.git
    cd
    ```

2.  **Instalar dependências:**
    O Poetry irá criar um ambiente virtual (`.venv/`) e instalar todas as dependências do projeto.
    ```bash
    poetry install
    ```

3.  **Configurar os hooks de pré-commit:**
    ```bash
    poetry run pre-commit install
    ```

## ⚙️ Como Usar

### Gerar uma Instância
```bash
poetry run python -m src.generator.cli --nodes 100 --density 0.1 --cv-vel 0.2 --output data/instances/synthetic/s_100_d01_cv02.json --seed 123
````

### Executar os Testes

```bash
poetry run pytest
```

### Executar um Experimento Remoto

*(Requer configuração prévia da máquina de execução conforme o protocolo)*

```bash
poetry run python src/orchestrator/ssh_executor.py --config configs/meu_experimento.yaml
```

## 📜 Protocolo Experimental

A metodologia completa, os objetivos e as métricas estão formalmente documentados em [docs/protocol/proto\_v3.1.1.md](docs/protocol/proto_v3.1.1.md).

Para um detalhamento completo das decisões de design e metodologia, veja o nosso [Documento de Arquitetura e Decisões](docs/00_architectural_overview.md).

## 📄 Licença

Este projeto é licenciado sob a licença MIT.

```
```
