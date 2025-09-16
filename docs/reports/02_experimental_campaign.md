# Desenho Experimental da Fase 1

## 1. Objetivo
O objetivo desta fase é caracterizar a performance de um conjunto de meta-heurísticas em um espaço de problemas controlado, conforme a hipótese central definida no protocolo `proto_v3.1.1`.

## 2. Fatores e Níveis
O experimento foi desenhado com os seguintes fatores:
- **Instâncias:** 15 instâncias sintéticas, variando em 3 níveis de tamanho (Small, Medium, Large), 3 níveis de densidade e 3 níveis de Coeficiente de Variação (CV). (Referenciar a lista completa em `plan.yaml`).
- **Heurísticas:** 7 algoritmos, incluindo um baseline Guloso, duas buscas locais e quatro meta-heurísticas de diferentes paradigmas. (Listar os algoritmos).
- **Orçamento Computacional:** 4 níveis de orçamento, definidos em número de avaliações da função-objetivo: {10k, 50k, 100k, 200k}.
- **Repetições (Seeds):** 5 sementes aleatórias distintas para cada combinação de fatores, para garantir a robustez estatística.

## 3. Desenho Experimental
O desenho é um **fatorial completo**, resultando em um total de 15 x 7 x 4 x 5 = 2.100 execuções planejadas.

## 4. Métrica de Resposta Primária
A performance será medida primariamente pelo **Hypervolume** da Frente de Pareto gerada por cada execução, considerando o vetor de objetivos `{ -FO1, |C|/|V|, CV_intra_cluster }`.
