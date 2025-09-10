# TC_005 — Smoke de Desempenho (Opcional)

**Objetivo**
Capturar **regressões grosseiras** de tempo e memória sem quebrar a CI.

**Pré-condições**
- Ambiente estável o suficiente para comparação aproximada.

**Passos**
1. Rodar um cenário leve (ex.: `n≈2000`, `p≈0.40`).
2. Medir tempo de parede simples (Python) e, se viável, RSS.
3. Comparar com baseline guardado em comentários ou arquivo leve.

**Critério**
- Se `tempo_atual > 2 × baseline`: marcar `xfail` com mensagem e **NÃO** falhar a pipeline.

**Notas**
- O baseline deve ser tomado em máquina similar (documente em `BENCH.md`).
