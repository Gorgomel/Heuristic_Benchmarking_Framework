# =========================
# Makefile — HPC Framework
# =========================
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
MAKEFLAGS += --no-builtin-rules

# --------- Ferramentas ----------
POETRY ?= poetry
RUN    := $(POETRY) run
DC     ?= docker compose

# --------- Instância padrão p/ smoke no CLI ----------
INSTANCE ?= data/instances/synthetic/n2000_p50.json.gz
K ?= 8
BETA ?= 0.03
SEED ?= 42
BUDGET ?= 60000
WORKDIR ?= data/results_raw
SMOKE_OUT := $(WORKDIR)/solvers_smoke

# --------- Ajuda ----------
.PHONY: help
help:
	@echo "Targets (local / poetry):"
	@echo "  install           - poetry lock+install (com extra metrics)"
	@echo "  fmt               - ruff --fix + black ."
	@echo "  lint              - ruff check . ; black --check . ; interrogate"
	@echo "  type              - mypy src"
	@echo "  test              - pytest"
	@echo "  cov               - pytest com cobertura (xml + term-missing)"
	@echo "  qa                - lint + type + cov"
	@echo "  docs              - mkdocs build"
	@echo "  serve             - mkdocs serve (dev)"
	@echo
	@echo "Smokes (pytest) — geram manifest.json e copiam artefatos se HPC_SMOKE_OUTDIR:"
	@echo "  smoke-tests       - pytest -m smoke (OUTDIR=$(SMOKE_OUT))"
	@echo "  metis-smoke       - somente METIS smoke (OUTDIR=$(SMOKE_OUT))"
	@echo "  kahip-smoke       - somente KaHIP smoke (OUTDIR=$(SMOKE_OUT))"
	@echo "  smoke-clean       - remove $(SMOKE_OUT)"
	@echo "  smoke-report      - mostra manifest.json se existir"
	@echo
	@echo "Smokes (CLI) — apenas roda o runner; não gera manifesto:"
	@echo "  smoke-cli-metis   - runner via CLI contra METIS"
	@echo "  smoke-cli-kahip   - runner via CLI contra KaHIP"
	@echo
	@echo "Manifest v1:"
	@echo "  manifest-v1-metis - empacota JSON -> manifest v1 (METIS)"
	@echo "  manifest-v1-kahip - empacota JSON -> manifest v1 (KaHIP)"
	@echo "  validate-v1       - valida 1+ manifests: make validate-v1 FILES=\"a.v1.json b.v1.json\""
	@echo "  validate-v1-all   - valida todos *.v1.json em $(WORKDIR)"
	@echo
	@echo "Docker compose:"
	@echo "  dc-build          - docker compose build"
	@echo "  dc-sh             - abre shell no serviço 'dev'"
	@echo "  dc-test           - roda testes no serviço 'test'"
	@echo "  dc-lint           - ruff + black --check no serviço 'dev'"
	@echo "  dc-type           - mypy no serviço 'dev'"
	@echo "  dc-docs           - mkdocs build --strict no serviço 'dev'"

# --------- Instalação (local) ----------
.PHONY: install
install:
	$(POETRY) lock
	$(POETRY) install -E metrics --no-interaction

# --------- Qualidade (local) ----------
.PHONY: fmt
fmt:
	$(RUN) ruff check . --fix
	$(RUN) black .

.PHONY: lint
lint:
	$(RUN) ruff check .
	$(RUN) black --check .
	$(RUN) interrogate -v

.PHONY: type
type:
	$(RUN) mypy src

.PHONY: test
test:
	$(RUN) pytest -q

.PHONY: cov
cov:
	$(RUN) pytest --cov=src --cov-report=term-missing --cov-report=xml

.PHONY: qa
qa: lint type cov

# --------- Docs (local) ----------
.PHONY: docs
docs:
	$(RUN) mkdocs build --strict

.PHONY: serve
serve:
	$(RUN) mkdocs serve -a 0.0.0.0:8000

.PHONY: install-docs
install-docs:
	$(POETRY) install --with docs --no-interaction

# --------- Smokes (pytest, com artefatos/manifesto) ----------
.PHONY: smoke-tests
smoke-tests:
	mkdir -p "$(SMOKE_OUT)"
	HPC_SMOKE_OUTDIR="$(SMOKE_OUT)" $(RUN) pytest -q -m smoke

# --------- Smoke (solvers específicos) ----------
.PHONY: metis-smoke
metis-smoke:
	mkdir -p "$(SMOKE_OUT)"
	HPC_SMOKE_OUTDIR="$(SMOKE_OUT)" $(RUN) pytest -q -m smoke -k metis

.PHONY: kahip-smoke
kahip-smoke:
	mkdir -p "$(SMOKE_OUT)"
	HPC_SMOKE_OUTDIR="$(SMOKE_OUT)" $(RUN) pytest -q -m smoke -k kahip

# --------- Relatório e limpeza ----------
.PHONY: smoke-report
smoke-report:
	@f="$(SMOKE_OUT)/manifest.json"; \
	if [ -f "$$f" ]; then \
	  echo "=== $$f ==="; (command -v jq >/dev/null && jq . "$$f") || cat "$$f"; \
	  echo; echo "Arquivos no OUTDIR:"; ls -lah "$(SMOKE_OUT)"; \
	else \
	  echo "manifest.json não encontrado em $(SMOKE_OUT)"; exit 1; \
	fi

.PHONY: smoke-clean
smoke-clean:
	rm -rf -- "$(SMOKE_OUT)"

# --------- Smokes (CLI, não geram manifesto) ----------
.PHONY: smoke-cli-metis
smoke-cli-metis:
	@command -v gpmetis >/dev/null 2>&1 || { echo "skip: gpmetis não está no PATH"; exit 0; }
	$(RUN) hpc-framework \
	  --instance "$(INSTANCE)" \
	  --algo metis \
	  --k $(K) --beta $(BETA) \
	  --budget-time-ms $(BUDGET) \
	  --seed $(SEED) \
	  --out $(WORKDIR)/smoke_metis.json \
	  --workdir $(WORKDIR) \
	  --log-level info

.PHONY: smoke-cli-kahip
smoke-cli-kahip:
	@command -v kaffpa >/dev/null 2>&1 || { echo "skip: kaffpa não está no PATH"; exit 0; }
	$(RUN) hpc-framework \
	  --instance "$(INSTANCE)" \
	  --algo kahip \
	  --k $(K) --beta $(BETA) \
	  --budget-time-ms $(BUDGET) \
	  --seed $(SEED) \
	  --kahip-preset fast \
	  --out $(WORKDIR)/smoke_kahip.json \
	  --workdir $(WORKDIR) \
	  --log-level info

# --------- Docker Compose ----------
.PHONY: dc-build
dc-build:
	$(DC) build

.PHONY: dc-sh
dc-sh:
	$(DC) run --rm dev bash

.PHONY: dc-test
dc-test:
	$(DC) run --rm test

.PHONY: dc-lint
dc-lint:
	$(DC) run --rm dev bash -lc "ruff check . && black --check ."

.PHONY: dc-type
dc-type:
	$(DC) run --rm dev bash -lc "mypy src"

.PHONY: dc-docs
dc-docs:
	$(DC) run --rm dev bash -lc "mkdocs build --strict"

# --------- Stubs p/ docs (evita erros em modo --strict) ----------
.PHONY: docs-stubs
docs-stubs:
	@mkdir -p docs/decisions docs/reports docs/protocol docs/testing docs/literature_review
	@printf "# HPC Framework\n\n_TODO._\n" > docs/index.md
	@printf "# Visão arquitetural\n\n_TODO._\n" > docs/00_architectural_overview.md
	@printf "# Plano do projeto e workflow\n\n_TODO._\n" > docs/01_project_plan_and_workflow.md
	@printf "# ADR 001: Linguagem de heurística\n\n_Status: draft._\n" > docs/decisions/001_choice_heuristic_language.md
	@printf "# ADR 003: Metodologia gerador/análise\n\n_Status: draft._\n" > docs/decisions/003_metodologia_gerador_e_analise.md
	@printf "# ADR 004: Testing e CI\n\n_Status: draft._\n" > docs/decisions/004_testing_and_ci.md
	@printf "# Relatório 01: Gerador de instâncias\n\n_TODO._\n" > docs/reports/01_instance_generator.md
	@printf "# Relatório 02: Campanha experimental\n\n_TODO._\n" > docs/reports/02_experimental_campaign.md
	@printf "# Protocolo v3.1.1\n\n_TODO._\n" > docs/protocol/proto_v3.1.1.md
	@printf "# TESTING\n\n_TODO._\n" > docs/testing/TESTING.md
	@printf "# CI\n\n_TODO._\n" > docs/testing/CI.md
	@printf "# TRACEABILITY\n\n_TODO._\n" > docs/testing/TRACEABILITY.md
	@echo "⚠️ Remova PDFs inexistentes do nav ou adicione-os em docs/literature_review." 1>&2

# --------- Validação via pytest (schema nos testes) ----------
.PHONY: validate-json
validate-json:
	$(RUN) pytest -q -k results_schema

# ---- Manifest / Schema ----
SCHEMA_V1 := specs/jsonschema/solver_run.schema.v1.json
MANIFEST_METIS_V1 := $(WORKDIR)/smoke_metis.v1.json
MANIFEST_KAHIP_V1 := $(WORKDIR)/smoke_kahip.v1.json

.PHONY: manifest-v1-metis
manifest-v1-metis:
	$(RUN) python scripts/pack_manifest_v1.py \
	  --in $(WORKDIR)/smoke_metis.json \
	  --out $(MANIFEST_METIS_V1)

.PHONY: manifest-v1-kahip
manifest-v1-kahip:
	$(RUN) python scripts/pack_manifest_v1.py \
	  --in $(WORKDIR)/smoke_kahip.json \
	  --out $(MANIFEST_KAHIP_V1)

# Valida 1+ manifests que você passar via VAR FILES="a.v1.json b.v1.json"
.PHONY: validate-v1
validate-v1:
	@if [ -z "$(strip $(FILES))" ]; then \
	  echo "Uso: make validate-v1 FILES=\"a.v1.json b.v1.json\""; exit 2; \
	fi
	$(RUN) python scripts/validate_manifest_v1.py \
	  --schema $(SCHEMA_V1) --in $(FILES)

# Valida todos os *.v1.json do diretório de resultados
.PHONY: validate-v1-all
validate-v1-all:
	@shopt -s nullglob; \
	files=($(WORKDIR)/*.v1.json); \
	if [ $$(( $${#files[@]} )) -eq 0 ]; then \
	  echo "Nenhum .v1.json encontrado em $(WORKDIR)"; exit 1; \
	fi; \
	echo "Validando: $${files[@]}"; \
	$(RUN) python scripts/validate_manifest_v1.py --schema $(SCHEMA_V1) --in $${files[@]}

# --------- pre-commit ----------
.PHONY: pre-commit-install
pre-commit-install:
	$(RUN) pre-commit install

# --------- Agregação e Estatística ----------
.PHONY: aggregate-manifests
aggregate-manifests:
	$(RUN) python scripts/aggregate_manifests.py --in-glob "$(WORKDIR)/*.v1.json" --out "$(WORKDIR)/manifest_index.csv"

.PHONY: stats-compare
stats-compare:
	$(RUN) python scripts/stats_compare.py --in-glob "$(WORKDIR)/*.v1.json" --a metis --b kahip --out-md "$(WORKDIR)/stats_compare.md"

# --------- Stubs API (mkdocstrings) ----------
.PHONY: docs-api-stubs
docs-api-stubs:
	@mkdir -p docs/api
	@test -f docs/api/generator_cli.md || echo -e "# generator.cli\n\n::: generator.cli" > docs/api/generator_cli.md
	@test -f docs/api/heuristics_greedy.md || echo -e "# heuristics.greedy\n\n::: heuristics.greedy" > docs/api/heuristics_greedy.md
	@test -f docs/api/hpc_framework_cli.md || echo -e "# hpc_framework.cli\n\n::: hpc_framework.cli" > docs/api/hpc_framework_cli.md
	@test -f docs/api/orchestrator_ssh_executor.md || echo -e "# orchestrator.ssh_executor\n\n::: orchestrator.ssh_executor" > docs/api/orchestrator_ssh_executor.md
