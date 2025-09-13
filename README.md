# Heuristic Benchmarking Framework (HBF)

[![CI](https://github.com/Gorgomel/Heuristic_Benchmarking_Framework/actions/workflows/ci.yml/badge.svg)](https://github.com/Gorgomel/Heuristic_Benchmarking_Framework/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-blue)](https://gorgomel.github.io/Heuristic_Benchmarking_Framework/)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)

Framework para benchmarking de heurísticas de **particionamento de grafos** com integração a **METIS (`gpmetis`)** e **KaHIP (`kaffpa`)**.
Inclui runner único, coleta de artefatos, manifesto JSON **v1** com schema, *smokes* determinísticos, *Makefile* de qualidade, **docs** (MkDocs) e **CI** (GitHub Actions).

**Repositório:** https://github.com/Gorgomel/Heuristic_Benchmarking_Framework

Autor: **Leonardo Brunno Sink Lopes** — <brunnosink2@gmail.com>
Licença: **MIT**

---

## Sumário
- [Instalação](#instalação)
- [Exemplos rápidos](#exemplos-rápidos)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Runner & Manifesto v1](#runner--manifesto-v1)
- [Testes & Qualidade](#testes--qualidade)
- [Documentação](#documentação)
- [Roadmap](#roadmap)
- [Agradecimentos & Terceiros](#agradecimentos--terceiros)
- [Como citar](#como-citar)
- [Licença](#licença)

---

## Instalação

### Requisitos
- **Python 3.11+**
- **Poetry** para gerenciar o ambiente
- (Opcional) **gpmetis** (METIS) e **kaffpa** (KaHIP) no `PATH` para executar os solvers

### Instalar dependências do projeto
```bash
poetry install -E metrics --no-interaction
poetry run pre-commit install  # hooks (ruff/black etc.)

Instalar solvers (opções)

Conda (recomendado, simples e cross-platform):

conda install -c conda-forge metis kahip
# isso fornece gpmetis e kaffpa

Ubuntu/Debian (APT):

# METIS (gpmetis está no pacote metis-tools)
sudo apt-get update
sudo apt-get install -y metis-tools

# KaHIP: disponível em versões mais novas do Ubuntu (kahip)
# se houver:
sudo apt-get install -y kahip

# Caso seu release não tenha o pacote 'kahip', compile a partir do código-fonte:
# https://github.com/KaHIP/KaHIP
# (build padrão gera o binário 'kaffpa')

> Os testes smoke do projeto verificam a presença de gpmetis/kaffpa e pulam automaticamente se estiverem ausentes.




---

Exemplos rápidos

# Qualidade local (lint + type + cobertura)
make qa

# Smokes (pytest) com artefatos e manifest.json
make smoke-tests
make smoke-report

# Runner via CLI (gera JSON simples)
make smoke-cli-metis
make smoke-cli-kahip

# Manifesto v1 a partir do JSON do runner + validação
make manifest-v1-metis
make validate-v1-all

# Agregar manifests em CSV + comparação estatística A vs B (Wilcoxon + bootstrap)
make aggregate-manifests
make stats-compare


---

Estrutura do projeto

src/
  hpc_framework/
    runner.py                 # orquestra 1 run e grava JSON simples
    solvers/
      common.py               # utilidades (.graph, exec, parsing…)
      metis.py                # wrapper gpmetis
      kahip.py                # wrapper kaffpa
scripts/
  pack_manifest_v1.py         # runner.json -> manifesto v1
  validate_manifest_v1.py     # valida contra JSON Schema
  aggregate_manifests.py      # glob *.v1.json -> CSV
  stats_compare.py            # Wilcoxon + bootstrap (mediana)
specs/
  jsonschema/
    solver_run.schema.v1.json # schema “congelado” (draft-07)
docs/
  mkdocs.yml + páginas        # documentação (Material for MkDocs)
tests/
  ...                         # unit, smokes, schema, runner, solvers
Makefile


---

Runner & Manifesto v1

1. Runner (hpc_framework.runner.run / CLI hpc-framework):

Exporta .graph, chama gpmetis ou kaffpa, mede tempo e coleta stdout/stderr.

Salva JSON “simples” (status, caminhos, cutsize_best, etc.).



2. Manifesto v1 (scripts/pack_manifest_v1.py):

Normaliza metadados, métricas (metrics.*), ambiente (env.*) e ferramentas (tools.*).

Validação por JSON Schema: specs/jsonschema/solver_run.schema.v1.json (draft-07).





---

Testes & Qualidade

Lint/Format: ruff, black, interrogate

Tipos: mypy

Testes: pytest (+ markers smoke)

Cobertura: pytest-cov (gera coverage.xml)

Makefile: fmt, lint, type, test, cov, qa, smoke-*, manifest-*, validate-*


make qa
make smoke-tests


---

Documentação

MkDocs Material (make docs) com páginas de API e seção de Testing/CI.

GitHub Pages: a pipeline de CI publica automaticamente em
https://gorgomel.github.io/Heuristic_Benchmarking_Framework/.


Desenvolvimento local:

make serve   # http://127.0.0.1:8000


---

Roadmap

🔜 Dashboards (Parquet → plots interativos).

🔜 Casos de teste adicionais (robustez e escalabilidade).

🔜 Suporte a novos solvers / formatos de instância.

🔜 Empacotamento PyPI.



---

Agradecimentos & Terceiros

METIS (gpmetis) — Karypis Lab.

KaHIP (kaffpa) — Karlsruhe High Quality Partitioning.

mkdocs-material, mkdocstrings, ruff, black, pytest, mypy, numpy/pandas/scipy, pre-commit.


> Este projeto não inclui esses binários; apenas integra com eles quando presentes no sistema.




---

Como citar

Se usar este framework em trabalhos acadêmicos, cite como:

L. B. S. Lopes. Heuristic Benchmarking Framework (HBF).
GitHub: https://github.com/Gorgomel/Heuristic_Benchmarking_Framework

(Se preferir, posso fornecer um CITATION.cff.)


---

Licença

Distribuído sob a licença MIT. Consulte LICENSE.
