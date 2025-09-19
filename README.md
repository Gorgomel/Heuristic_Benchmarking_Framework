# 🔨 FORJA — Reproducible Heuristic Benchmarking Framework

> **FORJA** é um **laboratório computacional encapsulado** para **benchmarking reprodutível** de algoritmos de **particionamento de grafos**.
> Foco em **justiça experimental**, **reprodutibilidade** e **análise guiada por protocolo**.

[![CI](https://github.com/Gorgomel/Heuristic_Benchmarking_Framework/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Gorgomel/Heuristic_Benchmarking_Framework/actions)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Version](https://img.shields.io/badge/version-0.8.0-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Por que FORJA?

Comparar meta-heurísticas costuma ser **frágil**: detalhes do ambiente, parâmetros implícitos e protocolos desiguais distorcem resultados.
O FORJA responde à pergunta central:

> **Como a topologia do grafo afeta o desempenho relativo de algoritmos de particionamento?**

**O que o FORJA garante:**
- ✅ **Justiça** – mesmos orçamentos e métricas para todos os algoritmos;
- 🔁 **Reprodutibilidade** – ambiente fixo, seeds controladas, contratos YAML;
- 🧪 **Rigor** – *smoke tests* determinísticos e CI mínima;
- 🧱 **Baselines sólidos** – heurísticas simples + SOTA como **METIS** (obrigatório) e **KaHIP** (opcional).

> 📚 Veja também: [CHANGELOG.md](./CHANGELOG.md) • [Docs (MkDocs)](./docs/index.md)

---

## 🧭 Sumário

- [Estrutura](#-estrutura)
- [Instalação](#️-instalação)
- [Smoke test](#-smoke-test)
- [Executando uma campanha](#️-executando-uma-campanha)
- [Qualidade & Reprodutibilidade](#-qualidade--reprodutibilidade)
- [Dados & Artefatos](#-dados--artefatos)
- [Citação e Licença](#-citação-e-licença)
- [Contribuindo](#-contribuindo)
- [Roadmap (próximos passos)](#-roadmap-próximos-passos)

---

## 🗂️ Estrutura

```
.
├─ configs/                # Planos de experimento (YAML, schema: forja-exp-v1)
├─ src/                    # Pacotes: hpc_framework, heuristics, solvers, runner
├─ tests/                  # Pytest (determinístico; KaHIP opcional)
├─ scripts/                # Orquestração (ex.: run_phase_1.sh)
├─ docs/                   # Documentação (MkDocs)
├─ data/
│  ├─ instances/synthetic/ # Instâncias exemplo (pequenas, versionadas)
│  └─ results_*            # Saídas de execuções (ignoradas no Git)
├─ .github/workflows/ci.yml# CI mínima (pip + pytest + METIS)
└─ CITATION.cff            # Metadados de citação
```

---

## ⚙️ Instalação

**Requisitos**: Linux/Ubuntu 22.04+, **Python 3.11+**, **Git**, **METIS** (`gpmetis` no `PATH`).
**Opcional**: **KaHIP** (`kaffpa` no `PATH`) — testes pulam caso ausente.

```bash
# Ubuntu 22.04
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip metis

# Ambiente virtual (recomendado)
python3.11 -m venv .venv
source .venv/bin/activate

# Instala o framework como pacote
pip install .
```

> ℹ️ **KaHIP**: siga as instruções do projeto para compilar/instalar (`kaffpa` no PATH).
> Se não houver, os testes/planos que dependem dele serão **pulados** com razão informativa.

---

## 🧪 Smoke test

Determinístico e rápido — garante que o ambiente está íntegro.

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
pytest -q
```

* Se **METIS** estiver ausente, os testes de `gpmetis` serão pulados.
* Se **KaHIP** estiver ausente, os testes de `kaffpa` serão pulados.

---

## 🏃‍♂️ Executando uma campanha

Os experimentos são definidos via **YAML** em `configs/`.
O script `scripts/run_phase_1.sh` orquestra o plano.

```bash
# padrão (usa configs/plan_phase_1.yaml)
./scripts/run_phase_1.sh

# ou passando um plano específico (ex.: piloto rápido)
./scripts/run_phase_1.sh configs/plan_phase_1_pilot.yaml
```

<details>
<summary><b>Exemplo: <code>configs/plan_phase_1.yaml</code></b></summary>

```yaml
---
schema: "forja-exp-v1"
experiment_id: "tcc-phase1"
description: "Greedy vs METIS (KaHIP opcional) em instâncias sintéticas"

rng:
  seeds: [42]

env:
  threads:
    omp: 1
    blas: 1
  require_bins: ["gpmetis"]
  allow_missing_bins: ["kaffpa"]

instances:
  base_dir: "data/instances/synthetic"
  include:
    - "n2000_p50.json.gz"
    - "modnull_n3000_p50.json.gz"
    - "modnull_n3500_p40.json.gz"
    - "mix_betas_n3000_p35_cv045.json.gz"
    - "n4000_cv_high.json.gz"
    - "n5000_cv_low.json.gz"
    - "wilson_tree_n10000.json.gz"
    - "n2000_dense_fast.json.gz"
  manifest_out: "data/results_raw/manifest_index.csv"
  fields: ["filename", "n", "m", "density", "cv_degree"]

solvers:
  greedy:
    enabled: true
    params: { delta_v: 0.1 }
    budget: { type: "time", seconds: 5 }

  metis:
    enabled: true
    k: 8
    budget: { type: "time", seconds: 5 }

  kahip:
    enabled: true           # roda local; no CI é pulado se ausente
    skip_if_missing: true
    k: 8
    imbalance: 0.03
    preset: "fast"
    budget: { type: "time", seconds: 5 }

protocol:
  repeats: 1
  randomize_instance_order: false
  write_partition_files: true

output:
  raw_dir: "data/results_raw"
  tables_dir: "data/results_parquet"
  log_level: "INFO"
  capture:
    git_sha: true
    hostname: true
    started_at: true
    finished_at: true
```

</details>

---

## 🔐 Qualidade & Reprodutibilidade

* **pre-commit**: trailing whitespace, EOF, YAML/JSON, Black, Ruff, Mypy, smoke (`pytest -m smoke`).

  ```bash
  poetry run pre-commit install -f
  poetry run pre-commit run -a
  ```
* **CI mínima** (GitHub Actions): `pip + pytest`, instala **METIS** via APT.
  Arquivo: `.github/workflows/ci.yml`.
* **Determinismo**: seeds + threads fixas; testes KaHIP/METIS com *skip-if-missing*.
* **Documentação**:

  ```bash
  poetry run mkdocs build --strict
  ```
* **Pacote de auditoria** (compacta código + instâncias pequenas + relatório):

  ```bash
  # gera índice/diagnóstico (opcional)
  ls -1 data/instances/synthetic > data/instances/instances_index.txt
  [ -x tools/diagnostics.sh ] && tools/diagnostics.sh > data/system_report.txt || true

  tar -czf FORJA_audit_$(date +%Y%m%d_%H%M).tar.gz \
    --exclude='site' --exclude='.venv' --exclude='dist' --exclude='__pycache__' \
    --exclude='.mypy_cache' --exclude='.ruff_cache' --exclude='*.egg-info' \
    --exclude='.git' --exclude='data/results_raw' --exclude='data/results_parquet' \
    --exclude='KaHIP' \
    pyproject.toml poetry.lock README.md CHANGELOG.md mkdocs.yml \
    .pre-commit-config.yaml .gitattributes .gitignore pytest.ini \
    .github/workflows/ci.yml \
    src tests configs scripts tools docs \
    data/instances/instances_index.txt \
    data/instances/synthetic/n2000_p50.json.gz \
    data/instances/synthetic/n2000_dense_fast.json.gz \
    data/system_report.txt
  ```

---

## 🗃️ Dados & Artefatos

* **Instâncias grandes**: não versionadas; use *releases assets* ou armazenamento externo.
* **Resultados**: `data/results_*` ignorados pelo Git (limpeza do repositório).
* **Contratos**: planos declarativos YAML (`schema: forja-exp-v1`) são a **interface oficial**.

---

## 📝 Citação e Licença

Este projeto é licenciado sob **MIT** (veja [LICENSE](LICENSE)).

Se usar o FORJA em pesquisa, **cite este repositório**.
Incluímos um [CITATION.cff](./CITATION.cff); no GitHub, use o botão **"Cite this repository"** na página do projeto.

---

## 🤝 Contribuindo

1. Crie sua branch a partir de `dev`;
2. Rode `pre-commit run -a` e `pytest -q` localmente;
3. Abra PR para `dev` (nunca direto para `main`);
4. Após revisão, `dev → main` via PR.

> Branch protegida: `main` aceita apenas PRs aprovados com CI.

---
