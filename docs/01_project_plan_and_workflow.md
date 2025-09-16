# Plano de Trabalho e Fluxo de Desenvolvimento

Este documento detalha a estratégia de implementação para as Fases 1 (Benchmarking de Heurísticas) e 2 (Validação em Simulação) do projeto. O desenvolvimento ocorrerá em duas frentes de trabalho paralelas, desacopladas por um contrato de dados bem definido.

## 1. Contrato de Interface ("Solução Estática")

A comunicação entre a Frente 1 e a Frente 2 é feita exclusivamente através de um arquivo de solução estática, atualmente em formato `.csv` ou `.parquet`.

* **Formato:** A primeira linha do arquivo deve conter um header de metadados, como `# schema_version=1.1`.
* **Campos Obrigatórios:** `vehicle_id` (int), `cluster_id` (int), `target_velocity` (float).
* **Campos Opcionais (para v2.0):** `lane_preference` (int), `start_time` (float).
* **Validação:** Um schema formal (Pydantic ou JSON-Schema) e um script (`scripts/check_solution.py`) serão fornecidos para validar a integridade dos arquivos de solução.
* **Exemplo:** Um arquivo de referência (`examples/solucao_schema_v1.1.csv`) será mantido no repositório para uso em testes de integração.

## 2. Frente de Trabalho 1 – Benchmarking de Heurísticas

* **Automação:** Um script `scripts/run_benchmarks.py` (ou alvo de `Makefile`) orquestrará a execução completa da Fase 1.
* **Saída Estruturada:** Cada execução `(instância, heurística, seed)` gerará um diretório em `results_best/`, contendo:
    * `best.json`: Métricas detalhadas da melhor solução encontrada.
    * `solution.csv`: O arquivo de solução que cumpre o contrato acima.
    * `meta.yaml`: Metadados da execução (versão do código, data/hora, etc.).

## 3. Frente de Trabalho 2 – Simulação SUMO/ROS2

| Tarefa | Checklist de Implementação |
| :--- | :--- |
| **Loader** | Implementar `utils.load_solution(path)` que valida o schema e carrega a solução. |
| **Mapa** | Utilizar um arquivo `.net.xml` fixo em `maps/`. |
| **Spawner** | Script `spawn.py` que lê o DataFrame da solução e usa a API TraCI do SUMO para criar e comandar os veículos. |
| **Estratégia**| Mínimo: `traci.vehicle.setSpeed`. Estendido: `traci.vehicle.changeLane`. |
| **Métricas** | Script de coleta que extrai dados da simulação (tempo de viagem, etc.). |
| **Automação**| Alvo `make sim INSTANCE=.../solution.csv`. |

## 4. Governança do Desacoplamento

* **Integração Contínua (CI):** O pipeline de CI terá jobs separados para cada frente de trabalho, garantindo que o desenvolvimento de uma não bloqueie a outra.
* **Versionamento do Contrato:** Qualquer alteração no formato do `solution.csv` exigirá um incremento na `schema_version`. O loader da Fase 2 deve ser programado para falhar rapidamente (`fail-fast`) se encontrar uma versão desconhecida.

## 5. Roadmap Incremental

* **Sprint 1:** Foco no setup básico da Fase 2: implementar o loader, o validador e executar uma simulação manual em SUMO com um arquivo de exemplo.
* **Sprint 2:** Integração de ponta a ponta para um caso pequeno: pipeline da Fase 1 gera um `solution.csv` que é consumido automaticamente pela simulação da Fase 2.
* **Sprint 3:** Escalar para instâncias maiores, medir o throughput do pipeline completo e otimizar parâmetros.
