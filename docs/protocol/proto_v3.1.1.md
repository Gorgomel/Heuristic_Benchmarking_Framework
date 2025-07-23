# Protocolo Experimental: Caracterização de Heurísticas (proto\_v3.1.1)

* **Versão:** 3.1.1
* **Data de Congelamento:** 23 de julho de 2025
* **Status:** **Go**. Protocolo final. Implementação autorizada.

## 1. Objetivo

Este trabalho visa desenvolver e validar um framework para a caracterização de performance multi‑objetivo de meta‑heurísticas aplicadas ao problema de clusterização de veículos. O objetivo principal é gerar um **Modelo Preditivo de Performance (MPP)** que informa a seleção de algoritmos em um sistema de coordenação dinâmica, mapeando características da instância a frentes de Pareto de custo‑benefício.

## 2. Hipótese Central

A topologia da instância (quantificada por **densidade** e **modularidade**) e a distribuição de atributos dos nós (quantificada pela **variação de velocidade**) são preditores estatisticamente significativos da performance relativa de diferentes meta‑heurísticas, onde a performance é medida pelo **Hypervolume** da Frente de Pareto gerada.

## 3. Definição Formal do Problema

Dado um grafo de visibilidade \$G=(V, E)\$, o problema consiste em encontrar uma partição \$C\$ do conjunto de vértices \$V\$ que **minimiza** o vetor de objetivos \$F(C)\$, sujeito a duas restrições rígidas.

### 3.1. Parâmetros Globais do Problema

* **Compatibilidade de Velocidade (`Δv`)**: diferença máxima de velocidade dentro de um cluster — **`Δv = 5.0 m/s`**.
* **Velocidade Máxima (`v_max`)**: velocidade máxima de um veículo — **`v_max = 16.0 m/s`**.

### 3.2. Vetor de Objetivos (a minimizar)

1. **`f1 = -FO1`** — negação de \$FO\_1 = \sum\_{k}|C\_k|,\min\_{v\_i\in C\_k}v\_i\$ (m/s·veículos).
2. **`f2 = |C|/|V|`** — fração de clusters (fragmentação).
3. **`f3 = CV_{\text{intra}}`** — coeficiente de variação médio das velocidades dentro dos clusters.

## 4. Protocolo Experimental

### 4.1. Algoritmos

Guloso (baseline), GRASP, SA, ILS, GA.

### 4.2. Instâncias

* **15 sintéticas** + **1 real** (RoadNet‑CA subgrafo).
* Tamanhos: Small (100‑250), Medium (500‑1500), Large (2500‑5000 nós).
* Parâmetros:

  * **Densidade**: <0.05 (baixa), 0.1–0.2 (média), >0.3 (alta).
  * **CV\_v**: <0.1 (baixa), 0.2–0.3 (média), >0.4 (alta).

### 4.3. Orçamento

* Avaliações `E ∈ {1e4, 5e4, 1e5, 2e5}`.
* Seeds por algoritmo: 5.
* `T_max = 900 s` wall‑clock.

### 4.4. Normalização

```json
{
  "neg_fo1":          {"min": "-(|V|*v_max)", "max": 0.0},
  "num_clusters_norm":{"min": "1/|V|",        "max": 1.0},
  "desvio_vel":       {"min": 0.0,             "max": "delta_v"},
  "overflow_policy":  "cap_and_flag"
}
```

* Ponto de referência HV: **{1.1, 1.1, 1.1}**.

### 4.5. Overflow

Valores truncados no `max`; flag `overflow=true`.

## 5. Contrato I/O

* **Entrada**: `config.yaml` com `(instância, heurística, E, seed)`.
* **Saída**:

```json
{
  "config": {…},
  "git_commit_hash": "…",
  "instance_metrics": {
    "nodes": 100,
    "edges": 450,
    "density": 0.09,
    "modularity": 0.81,
    "cv_vel": 0.15
  },
  "resultados": {
    "frente_pareto_final": [ {"neg_fo1": v1, "num_clusters_norm": v2, "desvio_vel": v3}, … ],
    "hypervolume": 0.81,
    "runtime_ms": 123456,
    "evaluations_total": 200000,
    "overflow": false,
    "history_log": [ … ]
  }
}
```

## 6. Análise Estatística

Regressão **Beta Hierárquica** com priors Horseshoe; transformação `clip(y,1e‑6,1‑1e‑6)`.

## 7. Reprodutibilidade

* Dependências fixas (`pyproject.toml` / Docker).
* `git_commit_hash` em cada resultado.
