# ADR-001: Linguagem para Implementação de Heurísticas

- **Status:** Decidido
- **Data:** 2025-07-24

## Contexto

A execução das meta-heurísticas (ILS, GA, SA, etc.) é a parte computacionalmente mais intensiva do projeto. A escolha da linguagem de implementação tem um impacto direto na performance de execução e na velocidade de desenvolvimento. Precisamos de uma estratégia que equilibre esses dois fatores para garantir o sucesso da Fase 1 da pesquisa.

## Opções Consideradas

1.  **Python Puro:** Implementar todas as heurísticas em Python, utilizando bibliotecas como `numpy` e `networkx` para operações otimizadas.
2.  **C++ com Bindings Python:** Implementar o núcleo de cada heurística em C++ de alta performance e criar uma camada de "binding" (usando `pybind11` ou `Cython`) para que possam ser chamadas a partir do nosso framework Python.

## Decisão

Para a Fase 1 do projeto, **todas as heurísticas serão implementadas em Python puro**.

## Justificativa

A prioridade da Fase 1 é a **velocidade de descoberta e iteração**. A complexidade de implementar, depurar e, principalmente, criar bindings para sete heurísticas diferentes em C++ representa um risco significativo para o cronograma e o foco do projeto. O ganho em velocidade de desenvolvimento em Python supera em muito o benefício da velocidade de execução nesta fase exploratória. A performance do Python é considerada suficiente para a campanha experimental planejada. A otimização de performance com C++ será reavaliada como uma atividade da Fase 2, e aplicada apenas aos algoritmos que se mostrarem mais promissores.
