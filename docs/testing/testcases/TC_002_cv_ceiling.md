# TC_002 — Teto de CV (1/3) e Warnings

**Objetivo**
Validar a política de **cap de CV = 1/3** (média central) e emissão de *warning* quando a meta solicitada excede o teto.

**Pré-condições**
- Python 3.11, CLI disponível
- Geração de atributo "velocidade" ativa

**Entradas (parametrizadas)**
- `cv_target ∈ {0.29, 0.33, 0.40}`

**Passos**
Para cada `cv_target`:
1. Executar o gerador produzindo o JSON.
2. Ler `instance_metrics.cv_vel_final` (ou campo equivalente).
3. Capturar logs/STDERR para warnings (quando capado).

**Resultados esperados**
- `0.29`: **sem warning**; erro relativo `|cv_final - 0.29| ≤ 0.02`.
- `0.33`: comportamento limite; pode existir *warning* informativo (aceitável).
- `0.40`: **warning de cap**; `cv_final ≈ 1/3 ± 0.02`.

**Notas**
- Documentado também no `README` (“Limites do CV”) e no `CHANGELOG`.
