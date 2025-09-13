# TESTING

## Camadas
1. **Unit**: funções puras (`compute_cutsize_edges_labels`, normalização, validações).
2. **Solvers**: wrappers `metis`/`kahip`, cobrindo: parâmetros inválidos, executável ausente, timeout, sucesso.
3. **Runner**: integração single-run (gera `.graph`, chama solver, lê partição, calcula cut).
4. **Smoke**: cenários leves e determinísticos; grava manifest.json (pytest) e `*.v1.json` (CLI+packer).
5. **Contrato/Schema**: validação `*.v1.json` contra `specs/jsonschema/solver_run.schema.v1.json`.

## Qualidade (portas de qualidade)
- `ruff` + `black` + `mypy` + `interrogate`
- `pytest -m smoke` deve passar local e no CI
- `validate_manifest_v1.py` sem erros
- Cobertura mínima (ex.: 60% no início, aumentando ao longo do projeto)

## Reprodutibilidade
- `_env_snapshot` embutido no manifest
- Poetries lockfile + versões de ferramentas no `tools` do manifest
- Seeds e parâmetros sempre serializados

## Estatística
- `scripts/stats_compare.py`: Wilcoxon + bootstrap do Δ mediano de cut.
- Artefatos: `data/results_raw/stats_compare.md`.
