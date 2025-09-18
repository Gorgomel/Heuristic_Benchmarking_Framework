# Metodologia do Gerador de Instâncias (v4.0)

## 1. Objetivo
O gerador de instâncias foi projetado para produzir grafos sintéticos para o benchmarking de heurísticas de clusterização. O design prioriza o controle paramétrico rigoroso, a reprodutibilidade e a escalabilidade, conforme definido no protocolo `proto_v3.1.1`.

## 2. Metodologia de Geração de Grafo
Para garantir a conectividade e a densidade alvo de forma eficiente, a construção do grafo segue um processo de duas etapas:
1.  **Garantia de Conectividade:** Uma árvore geradora aleatória (`random_labeled_tree` do NetworkX) é criada com `N` nós. Por definição, este grafo inicial é conexo e possui `N-1` arestas.
2.  **Ajuste de Densidade:** Arestas adicionais são inseridas aleatoriamente no grafo de forma iterativa e vetorizada, sem permitir laços ou arestas paralelas, até que o número total de arestas atinja o alvo definido pela densidade solicitada. Esta abordagem O(m) garante performance para grafos grandes e densos.

## 3. Metodologia de Geração de Velocidades
Para gerar velocidades de veículos com um Coeficiente de Variação (CV) alvo, foi implementada uma abordagem híbrida:
1.  **Distribuição Beta Reescalada:** Para CVs baixos e médios, amostras são retiradas de uma distribuição Beta cujos parâmetros (alpha, beta) são calculados para corresponder à média e variância desejadas. As amostras, no intervalo [0, 1], são então reescaladas para o intervalo de velocidades do protocolo [V_MIN, V_MAX].
2.  **Fallback Bimodal:** Se o CV alvo for matematicamente inatingível pela distribuição Beta, o sistema aciona um fallback para um método bimodal que distribui os veículos em dois grupos (velocidades próximas de V_MIN e V_MAX) para garantir a alta variância solicitada.

## 4. Interface de Uso (CLI)
O gerador é controlado via linha de comando, aceitando os seguintes parâmetros:
- `--nodes`: ...
- `--density`: ...
- `--cv-vel`: ...
- `--output`: ...
- `--epsilon`: ...
- `--seed`: ...
- `--verbose`: ...

## 5. Formato de Saída e Validação
A saída é um arquivo JSON único que adere a um schema formal (`specs/schema_input.json`). Antes de salvar, o gerador realiza uma validação automática para garantir a conformidade... (etc.)
