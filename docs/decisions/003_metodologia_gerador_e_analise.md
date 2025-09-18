# ADR-003: Metodologia Final para Geração de Instâncias e Análise de Heurísticas

- **Status:** Decidido
- **Data:** 2025-07-28

## 1. Contexto
Esta decisão consolida a base teórica e algorítmica para a Fase 1 do projeto, que visa construir um Modelo Preditivo de Performance (MPP). A metodologia precisa ser cientificamente defensável, robusta e alinhada com o estado da arte em otimização combinatória e ciência de redes.

## 2. Justificativa Teórica (Baseado em Revisão Bibliográfica)
[cite_start]A seleção de um algoritmo de otimização não é arbitrária, mas uma consequência dos **Teoremas "No Free Lunch" (NFL)**, que provam que a performance de um algoritmo depende da estrutura do problema [cite: 10-12]. [cite_start]A única forma de obter vantagem é através da especialização, alinhando a estratégia de busca (e.g., exploração vs. explotação) com as características da **Paisagem de Fitness** do problema [cite: 24-27].

[cite_start]A **Análise da Paisagem de Fitness (FLA)** fornece as ferramentas para medir a estrutura de um problema [cite: 45-47]. [cite_start]Conforme a literatura, a topologia do grafo do problema (nossa `densidade`, `modularidade`) molda diretamente a morfologia da paisagem (e.g., funis, platôs), que por sua vez favorece diferentes algoritmos [cite: 1623-1625, 1711-1713].
* [cite_start]**Grafos Esparsos → Funis:** Favorecem a **intensificação** (e.g., Busca Local, ILS) [cite: 1716, 1719-1720].
* [cite_start]**Grafos Densos → Platôs:** Favorecem a **exploração** (e.g., Algoritmos Genéticos) [cite: 1724, 1729-1730].
* [cite_start]**Grafos Modulares → Múltiplos Funis:** Favorecem algoritmos **híbridos** (e.g., Algoritmos Meméticos) que equilibram exploração e intensificação [cite: 1734, 1740-1742].

## 3. Decisões Finais de Implementação

### 3.1. Gerador de Instâncias (`generator/cli.py`)
Para criar instâncias com características controladas, a seguinte arquitetura foi finalizada:
* [cite_start]**Geração de Grafo Híbrida:** A geração do grafo será híbrida para máxima eficiência, uma estratégia validada pela literatura [cite: 2114-2115, 2176].
    * [cite_start]Para **grafos densos** ($m > 2n\log n$), será usado o método de **Amostragem por Rejeição**, que é mais simples e rápido neste regime [cite: 2127-2129, 2171].
    * [cite_start]Para **grafos esparsos**, será usado o **Método Construtivo**, que garante conectividade [cite: 2019-2022, 2162]. [cite_start]A árvore base será gerada via **Algoritmo de Wilson**, recomendado pela literatura como o melhor equilíbrio entre performance e simplicidade[cite: 2068, 2167].
* **Geração de Velocidades Híbrida:** A geração de velocidades com CV controlado também será híbrida:
    * [cite_start]Para **CV baixo/moderado**, será usada a **Distribuição Beta de 4 Parâmetros**, que possui solução analítica para a correspondência de momentos [cite: 449-451, 461].
    * [cite_start]Para **CV alto**, será usada uma **Mistura Bimodal Simétrica**, que é a abordagem teórica correta para criar alta variância em um intervalo fixo [cite: 465-468, 494].

### 3.2. Cálculo de Métricas (`instance_metrics`)
* [cite_start]**Modularidade:** A modularidade é uma métrica NP-difícil de otimizar [cite: 659-660]. Para a caracterização das instâncias, será usada a heurística **Greedy (CNM)** por ser determinística. [cite_start]O cálculo será condicional ao número de arestas para evitar gargalos de performance, uma estratégia pragmática justificada pela literatura [cite: 799-801, 806]. [cite_start]O **Método de Louvain**, por ser mais rápido mas não-determinístico, é mais adequado para a fase de análise exploratória[cite: 715, 758, 761].

## 4. Referências Externas
* `docs/literature_review/01_Busca_e_Problema.pdf`
* `docs/literature_review/02_Topologia_e_Paisagem.pdf`
* `docs/literature_review/03_Geracao_Grafos.pdf`
* ... (e os outros)
