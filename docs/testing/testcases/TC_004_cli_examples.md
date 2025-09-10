# TC_004 — Exemplos do README (Smoke CLI)

**Objetivo**
Verificar que os **exemplos do README** executam e produzem artefatos no local esperado.

**Pré-condições**
- CLI disponível
- `README.md` atualizado com pelo menos 2 exemplos reais

**Passos**
1. Rodar os comandos de exemplo em `tmp_path`.
2. Verificar a existência dos arquivos (`*.json` ou `*.json.gz`).
3. (Opcional) Abrir e checar 1–2 campos chave.

**Resultados esperados**
- Comandos executam sem erro.
- Artefatos existem no caminho indicado.
- JSON parseável.

**Notas**
- Sinalizar no README que `--verbose` pode reduzir throughput (não usar nos exemplos, salvo justificativa).
