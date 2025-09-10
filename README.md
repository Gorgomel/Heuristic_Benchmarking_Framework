# MPP-Framework: Framework de Caracterização de Heurísticas

Framework para a execução de experimentos e caracterização de performance multi-objetivo de meta-heurísticas aplicadas ao problema de clusterização de veículos autônomos.

Este projeto implementa o protocolo de pesquisa `proto_v3.1.1` para validar a tese de que o desempenho de diferentes algoritmos é uma função das características da instância do problema.

> 📌 Veja também: [CHANGELOG](./CHANGELOG.md)

---

## 🚀 Estrutura do Repositório

- **/docs**: Documentação formal (protocolo da pesquisa, relatórios técnicos).
- **/specs**: “Contratos” de dados (JSON Schemas e limites).
- **/src**: Código-fonte principal (`generator`, `heuristics`, `orchestrator`, etc.).
- **/tests**: Suíte automatizada (`pytest`) garantindo corretude.
- **/data**: Dados de entrada/saída. Instâncias em `data/instances/` são versionadas via **Git LFS**.
- **/notebooks**: Jupyter Notebooks para análise exploratória.
- **/scripts**: Utilitários para automação (execução remota, agregação, etc.).

---

## 🛠️ Instalação e Setup

Requisitos: **Python 3.11+**, **Git e Git LFS**, **Poetry**

1) **Clonar o repositório**
```bash
git clone https://github.com/Gorgomel/Performance_Predictive_Model_Framework.git
cd Performance_Predictive_Model_Framework
````

2. **Instalar dependências**

```bash
poetry install
```

3. **Configurar hooks de pré-commit**

```bash
poetry run pre-commit install
```

---

## ⚙️ Como Usar

### Gerar uma instância (CLI do gerador)

O gerador principal está em `src/generator/cli.py`. Ele produz um JSON (ou JSON.gz) com:

* **nodes**: id, velocidade (`[8,16]`) e posição 2D (`[0,1000]`),
* **edges**: arestas do grafo,
* **instance\_metrics**: métricas (densidade final, CV final, modularidade opcional etc.).

#### Como funciona (resumo técnico)

* **Conectividade base**: árvore geradora uniforme (UST) via **Algoritmo de Wilson** em $K_n$ (loop-erased random walks).
* **Complemento de arestas**: seleção por **índices lineares** do triângulo superior de $K_n$, com dispatcher:

  * `constructive` para regimes **raros** (baixa densidade),
  * `dense-fast` para regimes **densos** (pool maior e alta taxa de aceitação).
* **Velocidades**:

  * CV ≤ 0.29: **Beta 4-parâmetros** (moment matching), média recentrada e clip em $[8,16]$.
  * CV > 0.29: **mistura simétrica** nos extremos (bimodal leve) + ruído + correção de escala.
* **Validação**: saída **JSON-first** validada com **schema v1.1** em `specs/schema_input.json`.

#### Limites do CV

No suporte $[V_{\min},V_{\max}]=[8,16]$ com média no centro, o limite teórico é:

$$
\textbf{CV}_{\max} = \frac{V_{\max}-V_{\min}}{V_{\max}+V_{\min}} = \frac{16-8}{16+8} = \frac{1}{3} \approx 0.333\ldots
$$

Se `--cv-vel` exceder esse teto, o gerador **faz cap** em $1/3$ e emite **warning**.

> Para CVs maiores, é necessário **ampliar o intervalo** de velocidades e/ou **desacoplar a média** (não suportado por padrão).

#### Política de modularidade

A modularidade por método **greedy (CNM)** do NetworkX é **pulsada** por política de memória quando o grafo é grande:

$$
m \;>\; \min\big(1{,}200{,}000,\; 0{,}30 \cdot M\big)\quad \text{onde } M = \frac{n(n-1)}{2}.
$$

Quando o limite é excedido, a chave `modularity` sai como **`null`** por design (evita picos de RSS).

#### Comportamento de saída

* Se o caminho terminar com **`.json.gz`**, grava **Gzip texto**.
* Se terminar com **`.json`**, grava **JSON plano**.
* O caminho informado é respeitado **sem alterar a extensão**.

---

### Exemplos de uso (reprodutíveis)

> Dica: use `--verbose` apenas para debug (logs reduzidos melhoram throughput).

```bash
# Regime ralo saudável (10k nós, p=0.00025)
poetry run python -m src.generator.cli \
  --nodes 10000 --density 0.00025 --cv-vel 0.25 \
  --epsilon 50 --seed 123 \
  --output data/instances/synthetic/wilson_tree_10k.json.gz

# Denso médio (3k nós, p=0.50) – modularidade pulada por política de memória
poetry run python -m src.generator.cli \
  --nodes 3000 --density 0.50 --cv-vel 0.25 \
  --epsilon 50 --seed 1 \
  --output data/instances/synthetic/mod_null_n3000_p50.json.gz

# Denso médio (3.5k nós, p=0.40) – modularidade pulada
poetry run python -m src.generator.cli \
  --nodes 3500 --density 0.40 --cv-vel 0.25 \
  --epsilon 50 --seed 2 \
  --output data/instances/synthetic/mod_null_n3500_p40.json.gz

# Denso (2k nós, p=0.50) – modularidade pulada (limite fracionário)
poetry run python -m src.generator.cli \
  --nodes 2000 --density 0.50 --cv-vel 0.25 \
  --epsilon 50 --seed 42 \
  --output data/instances/synthetic/n2000_p50.json.gz

# CV acima do teto (4k nós, p=0.20, cv-vel=0.50) – será capado em ~0.333 com warning
poetry run python -m src.generator.cli \
  --nodes 4000 --density 0.20 --cv-vel 0.50 \
  --epsilon 50 --seed 9 \
  --output data/instances/synthetic/cv_high.json.gz
```

#### Amostra de performance (máquina do autor)

| Caso                             | Tempo (aprox.) | Pico RSS (aprox.) | Observações                            |
| -------------------------------- | -------------- | ----------------- | -------------------------------------- |
| 10k, p=0.00025                   | \~3.1 s        | \~97 MB           | Ralo saudável                          |
| 3k, p=0.50                       | \~41–42 s      | \~530 MB          | Modularidade pulada (gate)             |
| 3.5k, p=0.40                     | \~43 s         | \~580 MB          | Modularidade pulada (gate)             |
| 2k, p=0.50                       | \~19 s         | \~274 MB          | Modularidade pulada (gate fracionário) |
| 4k, p=0.20, cv-vel=0.50 (capado) | \~2–3 s        | \~?? MB           | CV capado em \~0.333 + warning         |

> Valores variam por hardware/SO; servem como referência de ordem de grandeza.

---

### Executar os testes

```bash
poetry run pytest
```

### Executar um experimento remoto

*(Requer configuração prévia da máquina de execução conforme o protocolo.)*

```bash
poetry run python src/orchestrator/ssh_executor.py --config configs/meu_experimento.yaml
```

---

## 📜 Protocolo Experimental

A metodologia completa, objetivos e métricas estão em
`docs/protocol/proto_v3.1.1.md`.

Para decisões de arquitetura, veja `docs/00_architectural_overview.md`.

---

## 📄 Licença

Este projeto é licenciado sob a licença MIT.

```
