# Rastreabilidade Teste ↔ Requisito

| Requisito / Decisão | Teste(s) | Evidência / Saída |
|---|---|---|
| Schema de entrada/saída v1.1 | `tests/test_generator.py::test_schema_output_v11` | `data/results_raw/*.json` compatíveis |
| Conectividade e densidade | `tests/test_generator.py::test_density_bisection` | `density_final` dentro de `δ_p` |
| Gate de modularidade (dinâmico) | `tests/test_generator.py::test_modularity_gate_regression` | `modularity is None` quando m > limite |
| Cap de CV (≤ 1/3) | `tests/test_generator.py::test_cv_capping` | warning + `cv_final≈1/3±0.02` |
| CLI JSON-first e compressão `.gz` | `tests/test_sanity.py::test_cli_json_gz` | arquivos `.json`/`.json.gz` válidos |
| Freeze do schema | `tests/test_generator.py::test_schema_freeze` | versão esperada carregada |
