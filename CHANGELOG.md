# CHANGELOG

> Todas as mudanças notáveis neste projeto serão documentadas aqui.
> Versão atual: **v6.1.0** — 2025-08-20

## v6.1.0

### Destaques

* **Wilson-first**: construção da árvore geradora via Algoritmo de Wilson (UST em $K_n$), determinística dado o seed, com arestas canonicalizadas e ordenadas (reprodutibilidade total).
* **Dispatcher de arestas**: seleção automática entre `constructive` e `dense-fast` usando limiar prático $m_\text{target} > 2n\log n$.
* **JSON-first validado (schema v1.1)**: saída validada contra `specs/schema_input.json`; campo `modularity` agora **pode ser `null`** quando o cálculo for pulado por política de tamanho.
* **Guard-rails de modularidade**: cálculo via CNM (NetworkX) só é executado se $|E| \le \min(1{,}200{,}000,\; 0{,}30\cdot M)$, onde $M=n(n-1)/2$. Evita picos de memória ao materializar `Graph`.
* **CV de velocidades, com cap e aviso**: como as velocidades estão em $[8,16]$ com média fixada no centro (12), o **CV teórico máximo é $1/3 \approx 0{,}3333$**. Pedidos acima disso são **capados** para $1/3$ com `logging.warning`.

### O que mudou

* **Construção de grafo**

  * Árvore base por Wilson (loop-erased random walks) evitando auto-laços e conectando caminho invertido ao primeiro nó na árvore.
  * Complemento de arestas por **índices lineares** no triângulo superior; queima de máscara só no que é usado; batches adaptativos; `dense-fast` com pools agressivos em grafos densos.
* **Métricas**

  * `modularity`: retorna número apenas para grafos “pequenos”; caso contrário `null` por política (evita RSS alto).
* **Gerador de velocidades**

  * **CV baixo (≤ 0.29)**: Beta 4-parâmetros (moment matching) + realinhamento de média + clip.
  * **CV alto (> 0.29)**: mistura simétrica nos extremos $[8,16]$ + ruído leve + correção de escala, recentrando a média.
  * **Auditoria**: `WARNING` se $|CV_{emp}-CV_{alvo}|>0.02$ com $n\ge100$; `WARNING` se alvo > $1/3$ (cap aplicado).

### Compatibilidade (schema v1.1)

* Consumidores do JSON **devem aceitar `modularity: null`** quando o cálculo é pulado.
* Demais campos mantêm semântica anterior; posições `pos` continuam uniformes em $[0,1000]^2$.

### Amostras de desempenho (máquina do autor)

|      n | densidade p | modo           | wall-time   | Max RSS      | Observações                                     |
| -----: | :---------- | :------------- | :---------- | :----------- | :---------------------------------------------- |
| 10 000 | 0.00025     | `constructive` | **3.09 s**  | **\~97 MB**  | regime ralo saudável                            |
|  3 000 | 0.50        | `dense-fast`   | **41.94 s** | **\~534 MB** | modularidade pulada pelo gate                   |
|  3 500 | 0.40        | `dense-fast`   | **42.87 s** | **\~578 MB** | modularidade pulada pelo gate                   |
|  3 000 | 0.35        | `dense-fast`   | **28.87 s** | **\~380 MB** | `cv-vel=0.45` → **capado** para $1/3$ (warning) |
|  2 000 | 0.50        | `dense-fast`   | **18.86 s** | **\~274 MB** | modularidade pulada (limite dinâmico = 599 700) |

> Valores medidos com `/usr/bin/time -v`; `Max RSS` reportado pelo SO.

### Notas de migração

* Se você persistia ou exigia `modularity` sempre numérico, ajuste para aceitar `null` em instâncias grandes.
* Se passar `--cv-vel` acima de $1/3$ (com média no centro), o gerador **capará** para $1/3$ e emitirá `WARNING`. Para CVs maiores, seria necessário **mudar o suporte** $[V_\min,V_\max]$, **desacoplar** a média, ou **relaxar** o clip (não recomendado).

### CLI (exemplos)

```bash
# instância rala
python -m src.generator.cli --nodes 10000 --density 0.00025 --cv-vel 0.25 \
  --epsilon 50 --seed 123 --output data/instances/synthetic/wilson_tree_10k.json.gz

# instância densa (gate de modularidade deve pular)
python -m src.generator.cli --nodes 3000 --density 0.50 --cv-vel 0.25 \
  --epsilon 50 --seed 1 --output data/instances/synthetic/mod_null_n3000_p50.json.gz
```
