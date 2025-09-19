````markdown
# FORJA — A Reproducible Heuristic Benchmarking Framework

> **FORJA** é um laboratório computacional para a análise empírica e reprodutível de algoritmos de particionamento de grafos.

[![CI Status](httpsd://github.com/SEU_USUARIO/SEU_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/SEU_USUARIO/SEU_REPO/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Version](https://img.shields.io/badge/version-0.8.0-blue)

---

## 🎯 Qual Problema o FORJA Resolve?

A comparação de meta-heurísticas é notoriamente difícil. Resultados frequentemente dependem de ambientes de execução específicos, parâmetros não documentados e protocolos de teste que não são justos, tornando a ciência da computação menos reprodutível.

O **FORJA** foi criado para resolver este problema, oferecendo um ambiente padronizado e automatizado para responder a uma pergunta central: **Como a topologia de um grafo afeta o desempenho relativo de diferentes algoritmos de particionamento?**

O objetivo é sair do "inferno da configuração" e permitir que pesquisadores e engenheiros foquem na análise, com a confiança de que os experimentos são:
* **Justos:** Todos os algoritmos competem sob as mesmas regras (orçamentos de tempo, métricas).
* **Reprodutíveis:** O ambiente encapsulado (Docker) e os contratos de dados (YAML) garantem que os resultados possam ser replicados.
* **Relevantes:** A comparação inclui não apenas heurísticas clássicas, mas também baselines de estado da arte como METIS e KaHIP.

## ✨ Funcionalidades Principais

* **Execução via Contrato:** Defina toda a sua campanha experimental em um único arquivo YAML.
* **Portfólio Extensível:** Compare suas próprias heurísticas com um núcleo já implementado (Greedy, SA, GA) e baselines (METIS, KaHIP).
* **Reprodutibilidade Garantida:** Ambiente Docker, dependências travadas com Poetry e schemas de validação de dados.
* **Resultados Prontos para Análise:** Saídas em formatos limpos (Parquet/JSON) com metadados de proveniência completos.
* **Qualidade de Código Assegurada:** Testes automatizados com `pytest` e `pre-commit` para garantir a integridade do framework.

## 🚀 Começando (Quick Start)

### 1. Pré-requisitos (Ambiente Ubuntu 22.04)

O FORJA requer Python 3.11+ e solvers externos.

```bash
# Instalar dependências de sistema
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip metis

# Opcional, mas recomendado: Instalar KaHIP (se não instalado, os testes serão pulados)
# Siga as instruções de compilação em [https://github.com/KaHIP/KaHIP](https://github.com/KaHIP/KaHIP)
````

### 2\. Instalação

Recomendamos a instalação em um ambiente virtual.

```bash
# Crie e ative o ambiente virtual
python3.11 -m venv .venv
source .venv/bin/activate

# Instale o pacote FORJA
pip install .
```

### 3\. Teste de Sanidade (Smoke Test)

Verifique se tudo está funcionando corretamente. Este teste é determinístico.

```bash
# Fixa threads para reprodutibilidade e executa os testes
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 pytest -q
```

-----

## 🔬 Como Usar: Executando uma Campanha

A execução de experimentos é controlada por arquivos de plano em `configs/`.

### 1\. Entendendo o Contrato (`forja-exp-v1`)

O arquivo `configs/plan_phase_1.yaml` é um exemplo completo que define a instância, os algoritmos, os orçamentos e as saídas.

```yaml
schema: "forja-exp-v1"
experiment_id: "tcc-phase1"
description: "Greedy vs METIS (KaHIP opcional) em instâncias sintéticas"
# ... (restante do YAML como no seu original)
```

### 2\. Executando o Plano

Um script utilitário orquestra a execução.

```bash
# Executa o plano padrão
./scripts/run_phase_1.sh

# Executa um plano customizado (ex: um piloto rápido)
./scripts/run_phase_1.sh configs/plan_phase_1_pilot.yaml
```

> **Dica:** Para criar um piloto, copie um plano existente, reduza a lista de instâncias para 1 ou 2, e use um único `seed`. Isso permite validar o pipeline em segundos.

-----

## 📂 Estrutura do Projeto

O repositório está organizado para separar código, configuração, dados e documentação de forma clara.

```
configs/      # Planos de experimento (YAML)
data/         # Instâncias de exemplo e manifestos (resultados grandes são ignorados)
docs/         # Documentação (MkDocs)
scripts/      # Scripts de execução e utilitários
src/          # Código-fonte do framework (pacote hpc_framework)
tests/        # Suíte de testes (pytest)
pyproject.toml # Definição do projeto e dependências (Poetry)
```

## 🔐 Qualidade e Reprodutibilidade

Este projeto leva a reprodutibilidade a sério. Utilizamos:

  * **pre-commit:** Para garantir a qualidade e o estilo do código antes de cada commit.
  * **GitHub Actions:** Para rodar os testes de forma automatizada a cada push.
  * **Docker:** Para encapsular o ambiente completo e garantir a re-execução em qualquer máquina.
  * **Versionamento de Artefatos:** Cada resultado e figura é gerado com metadados que incluem o hash do commit do Git, garantindo a proveniência.

## 📝 Licença e Citação

Este projeto é distribuído sob a licença **MIT**. Se você utilizar o FORJA em sua pesquisa, por favor, cite este trabalho. Um arquivo `CITATION.cff` é fornecido para facilitar a citação.


-----

```
```
