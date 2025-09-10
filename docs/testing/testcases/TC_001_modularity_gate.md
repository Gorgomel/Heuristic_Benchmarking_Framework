# TC_001 — Regressão do Gate de Modularidade

**Objetivo**
Garantir que, quando o grafo ultrapassa o **limite dinâmico de modularidade** (definido e documentado no código/CHANGELOG), o campo `instance_metrics.modularity` seja **`null`** no JSON gerado.

**Pré-condições**
- Python 3.11
- CLI do gerador instalado (`poetry run <cli>` ou entry-point equivalente)
- `jsonschema` disponível
- Semente fixa no teste

**Passos (Given–When–Then)**
1. *Given* um cenário “denso” (ex.: `n≈3000`, `p≈0.50`) com parâmetros do gerador que acionem o limite.
2. *When* o CLI é executado gerando um arquivo `*.json.gz` em `tmp_path`.
3. *Then* o JSON parseado apresenta `instance_metrics.modularity == null`.
4. (Opcional) *And* os logs contêm menção ao gate.

**Resultados esperados**
- `modularity` presente e `null`.
- JSON válido no `schema_input.json` (v1.1).

**Notas**
- Não validar fórmula específica do limite aqui — apenas o **efeito** (pular modularidade).
- Seeds fixas para reduzir variação.
