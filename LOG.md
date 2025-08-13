## 2025-07-24

**Assunto:** Finalização da Infraestrutura de Execução Remota e Design do Gerador.

**Infraestrutura:**
- O plano inicial de usar Docker no desktop foi inviabilizado pela falta de suporte à virtualização de hardware (VT-x/AMD-V). A tentativa de usar VirtualBox também falhou pela mesma razão.
- **Decisão Crítica:** Pivotamos a estratégia para usar WSL1 no desktop. Isso oferece um ambiente Linux consistente com o de desenvolvimento (WSL2), resolvendo o principal risco de reprodutibilidade da abordagem "Nativa Windows".
- **Depuração SSH:** Encontramos múltiplos problemas na conexão via script:
    1. `AuthenticationException`: Resolvido especificando o caminho da chave `id_ed25519` no script.
    2. `ValueError` (criptografia): A chave `id_rsa` era do tipo DSA, que é obsoleto. Resolvido gerando e usando uma nova chave ED25519.
    3. `Host Key Verification Failed`: Resolvido conectando-se manualmente uma vez do desktop ao GitHub para salvar a chave do host.
    4. `poetry: command not found`: Resolvido usando o caminho absoluto (`/home/user/.local/bin/poetry`) no script, pois a sessão SSH não-interativa não carrega o `.bashrc`.

**Gerador de Instâncias:**
- A primeira versão do `build_graph` usando um loop `while` era `O(n*m)` e causou um crash de falta de memória (`OOM Killer`) no cenário de 5000 nós.
- **Decisão de Design:** O algoritmo foi reescrito para uma abordagem vetorizada com NumPy para garantir performance e escalabilidade, que deve ser testada no próximo piloto.
- O gerador de velocidades também foi refinado para usar uma distribuição Beta com fallback bimodal para garantir a geração de CVs altos, um requisito do protocolo.

**Próximo Passo:** Rodar o piloto final com o gerador otimizado para calibrar o `bounds.json`.

**Assunto:** Finalização do Plano Experimental da Fase 1.

- **Marco:** O arquivo `configs/plan_phase_1.yaml` foi finalizado.
- **Escopo:** A campanha experimental completa foi definida, totalizando **2.100 execuções** (15 instâncias sintéticas x 7 heurísticas x 4 orçamentos x 5 seeds).
- **Status:** O orquestrador (`scripts/pipeline.py`) e o executor (`src/orchestrator/ssh_executor.py`) estão prontos para consumir este plano.
- **Próximo Passo:** Com a infraestrutura e o plano definidos, o próximo grande trabalho é a implementação modular de cada uma das 7 heurísticas em `src/heuristics/`.

**Assunto:** Decisão sobre a linguagem de implementação das Heurísticas.

- **Questão:** Avaliamos a possibilidade de implementar as heurísticas da Fase 1 em C++ para maximizar a performance de execução.
- **Opções Consideradas:**
    1.  **Python Puro:** Rápido para desenvolver, ecossistema científico rico (`numpy`, `networkx`), mas lento na execução.
    2.  **C++ com Bindings:** Rápido na execução, mas com altíssima complexidade de desenvolvimento, integração (`pybind11`) e manutenção.
- **Decisão:** Manter o desenvolvimento da **Fase 1 inteiramente em Python**.
- **Justificativa:** O gargalo do projeto nesta fase é a **velocidade de descoberta e desenvolvimento**, não o tempo de CPU. É mais importante implementar e testar rapidamente as 7 heurísticas para validar a tese. Migrar para C++ agora seria uma otimização prematura que colocaria o cronograma em risco. A performance de execução do Python é "suficiente" para a campanha experimental na máquina fixa. A otimização em C++ será considerada na Fase 2, apenas para os algoritmos "campeões".

----------------------------------------

## 2025-07-25

**Assunto:** Consolidação da Fase 0 - Registro de Decisões e Dificuldades na Configuração da Infraestrutura e do Gerador.

**Status:** A fase de configuração está conceitualmente finalizada (Protocolo v5.4). Esta entrada documenta o caminho percorrido.

### 1. Evolução da Arquitetura de Execução

O objetivo era criar um pipeline de execução remota, separando o ambiente de desenvolvimento (notebook) do de execução (desktop). O processo foi marcado por uma restrição de hardware crítica que forçou múltiplas mudanças de plano.

* **Plano Inicial (Docker):** A primeira proposta era usar Docker no desktop para garantir 100% de reprodutibilidade.
    * **Dificuldade:** O desktop não possuía suporte à virtualização de hardware (VT-x/AMD-V), confirmado pelo comando `systeminfo`.
    * **Consequência:** Inviabilizou o uso do Docker Desktop (tanto com backend WSL2 quanto Hyper-V) e de outras soluções baseadas em VM, como o VirtualBox. **Decisão:** O plano baseado em containers foi abandonado.

* **Pivô 1 (Execução Nativa no Windows):** A primeira alternativa foi instalar um ambiente Python diretamente no Windows 10 do desktop.
    * **Dificuldade:** Essa abordagem apresentava um alto risco de **baixa reprodutibilidade**, pois o ambiente de execução (Windows) seria fundamentalmente diferente do de desenvolvimento (Linux via WSL2).
    * **Consequência:** Risco de "environment drift" e de resultados não-reproduzíveis. **Decisão:** A abordagem foi considerada de alto risco e preterida em favor de uma solução melhor.

* **Pivô 2 (WSL1 - Solução Adotada):** A solução final foi usar o **WSL1** no desktop.
    * **Justificativa:** WSL1 não requer virtualização de hardware e provê um ambiente Linux, criando uma alta consistência com o ambiente de desenvolvimento WSL2 do notebook. Foi o melhor equilíbrio entre reprodutibilidade e as restrições de hardware.

* **Depuração da Conexão SSH:** A conexão remota via script apresentou uma cascata de problemas que foram resolvidos sequencialmente:
    1.  **`AuthenticationException`:** O script não encontrava a chave SSH. Resolvido especificando o caminho explícito da chave no código.
    2.  **`ValueError` Criptográfico:** A chave `id_rsa` era do tipo DSA (obsoleto). Resolvido gerando e usando uma nova chave `ed25519`.
    3.  **Conflito de Portas:** O SSH para o IP do desktop conectava ao servidor do Windows, não ao do WSL1. Resolvido configurando o servidor SSH do WSL1 para operar na porta `2222`.
    4.  **`command not found`:** O `PATH` do ambiente SSH não-interativo não continha o `poetry`. Resolvido usando o caminho absoluto (`/home/user/.local/bin/poetry`) no script.

### 2. Evolução do Gerador de Instâncias

O design do gerador (`src/generator/cli.py`) passou por múltiplas iterações para resolver problemas de performance, uso de memória e correção metodológica.

* **Performance (`build_graph`):**
    * **Dificuldade:** A implementação inicial com um loop `while` que adicionava arestas uma a uma era `O(m)` em teoria, mas a sobrecarga do Python e do `networkx.has_edge()` a tornava inviável, levando **mais de uma hora** e sendo morta por falta de memória (`Killed`).
    * **Decisão:** Adotamos uma abordagem **"JSON-first"**, onde a lógica principal opera sobre listas de arestas em NumPy. A solução final utiliza uma **máscara booleana** para rastrear arestas disponíveis e **amostragem em lotes**, garantindo baixo consumo de memória (RAM constante) e alta velocidade (execução em segundos).

* **Metodologia (`generate_velocities`):**
    * **Dificuldade:** A geração de velocidades com um Coeficiente de Variação (CV) alvo se mostrou instável. O método `Normal + clip` distorcia o CV. A Distribuição Beta tinha um domínio limitado.
    * **Decisão:** A solução final é um **método híbrido robusto**: (1) Para CVs baixos (≤ 0.29), usa-se o `Normal-clip` com uma **correção única pós-clip** para restaurar a média e o desvio padrão. (2) Para CVs altos (> 0.29), usa-se uma **distribuição bimodal** cuja proporção é calculada analiticamente via **busca por bisseção** para atingir o CV alvo com precisão.

### 3. Evolução do Protocolo e Contrato de Dados

* **Foco da Pesquisa:** A meta inicial de "encontrar o melhor algoritmo" foi refinada para "criar um **Modelo Preditivo de Performance (MPP)**", uma tese mais forte.
* **Contrato de Dados (`schema_input.json`):** O schema evoluiu de uma estrutura simples para uma mais completa, incluindo:
    * O campo `epsilon`.
    * Limites de valor (`minimum`, `maximum`) para velocidades e posições.
    * Um bloco `instance_metrics` para registrar os parâmetros de geração e as propriedades finais da instância, garantindo total transparência e auditabilidade.
    * A permissão de `null` para a modularidade em casos de grafos muito grandes, uma decisão de design consciente.

**Status Atual:** O gerador está conceitualmente finalizado e pronto para a implementação do `Protocolo v5.4`. Toda a infraestrutura está configurada e testada.

**Assunto:** Decisão de Refatoração do Gerador de Grafos para uma Estratégia Híbrida, com Base em Revisão Bibliográfica.

**Contexto:**
Após a implementação de um gerador de grafos funcional (`Protocolo v5.4`), surgiu a necessidade de validar se a metodologia adotada (árvore via Prüfer + adição de arestas) era a mais robusta e eficiente. Foi realizada uma pesquisa bibliográfica para embasar a decisão de "congelar" o gerador.

**Análise da Literatura (Ref. "Relatório Bibliográfico sobre a Geração de Grafos Aleatórios Conexos"):**

A pesquisa (arquivo: `Geração de Grafos Aleatórios Conexos_.pdf`) revelou os seguintes pontos-chave:

1.  **Duas Metodologias Principais:** A literatura valida duas abordagens para o problema:
    * [cite_start]**Método Construtivo (Aumento de Árvore):** Garante conectividade por design e é ideal para grafos **esparsos** [cite: 750-752]. Nossa implementação atual se encaixa nesta categoria.
    * **Amostragem por Rejeição (Erdős-Rényi):** Gera um grafo com `m` arestas e testa a conectividade, repetindo se falhar. [cite_start]É extremamente eficiente para grafos **densos**, onde a probabilidade de desconexão é "desprezível" [cite: 857-859, 901-902].

2.  **Quadro de Decisão:** A escolha ótima do algoritmo é uma função da densidade do grafo. [cite_start]O limiar crítico é o de conectividade de Erdős-Rényi, $m_{crit} \approx \frac{1}{2}n\log n$[cite: 855, 907].
    * Se `m_alvo <= m_crit`, o método construtivo é o único viável.
    * [cite_start]Se `m_alvo >> m_crit`, a amostragem por rejeição é mais simples e rápida[cite: 908].

3.  [cite_start]**Otimização do Método Construtivo:** Para a geração da árvore base, a literatura aponta o **Algoritmo de Wilson** como uma alternativa superior à Sequência de Prüfer em termos de equilíbrio entre performance e simplicidade de implementação prática[cite: 897].

**Decisão Arquitetônica (Protocolo v6.0):**

Com base na análise, foi decidido **refatorar o gerador de grafos para uma estratégia híbrida**, em vez de usar um único método para todos os casos.

1.  **Implementação de um "Dispatcher":** A função `build_edge_list` será transformada em um "dispatcher". Ela calculará o limiar de conectividade $m_{crit}$ e, com base na `target_density`, escolherá dinamicamente qual algoritmo de geração utilizar.

2.  **Adição do Método de Rejeição:** Será criada uma nova função, `_build_by_rejection`, que implementará o algoritmo de amostragem por rejeição, a ser usada para os casos de alta densidade.

3.  **Manutenção do Método Construtivo:** Nossa implementação atual (Prüfer/heapq + adição de arestas) será mantida para os casos de baixa e média densidade.

**Justificativa da Escolha:**
Esta abordagem híbrida é superior porque:
* [cite_start]**Alinha-se com o Estado da Arte:** Segue diretamente a recomendação principal da revisão bibliográfica [cite: 906-908].
* **Garante Performance Ótima:** Usa o algoritmo mais rápido e simples para cada regime de densidade (rejeição para densos, construtivo para esparsos).
* **Aumenta a Robustez:** Garante que o gerador não ficará preso em um regime computacionalmente intratável, como seria o caso de usar o método construtivo em grafos muito densos ou a rejeição em grafos muito esparsos.

**Próximos Passos:**
1.  Implementar a lógica do dispatcher em `build_edge_list`.
2.  Implementar a nova função `_build_by_rejection`.
3.  Manter a função `_prufer_to_edges` e a lógica de adição de arestas como o "braço" construtivo do gerador.

**Assunto:** Definição da Arquitetura Final para o Módulo de Geração de Velocidades (`generate_velocities`).

**Contexto:**
Após a conclusão da pesquisa bibliográfica sobre o Tema 2 (arquivo: `Geração de Amostras Controladas_.pdf`), ficou evidente que a implementação atual da função `generate_velocities` (Protocolo v5.4), embora funcional, não era a mais robusta nem a mais alinhada com as melhores práticas teóricas. A abordagem "Normal-clip-correção" foi identificada como um proxy para um problema numericamente complexo, para o qual a literatura oferece soluções analíticas superiores.

**Análise Crítica e Decisão Arquitetônica (Protocolo v6.1):**

Com base na análise do relatório, foi decidido refatorar completamente a lógica de geração de velocidades, adotando uma arquitetura modular e híbrida que espelha diretamente as recomendações da literatura.

1.  **Abordagem Híbrida ("Dispatcher"):** A função principal `generate_velocities` atuará como um "dispatcher", selecionando o método de amostragem mais apropriado com base no `target_cv`:
    * **Se `target_cv <= 0.29`:** Será utilizado um amostrador baseado na **Distribuição Beta de 4 Parâmetros**.
    * **Se `target_cv > 0.29`:** Será utilizado um amostrador baseado em uma **Mistura Bimodal Simétrica de duas distribuições Beta**.

2.  **Módulo para CV Baixo/Moderado (`samplers/beta_4p.py`):**
    * **Lógica:** Implementará a solução analítica e de tempo constante `O(1)` para a correspondência de momentos.
    * **Passos:** (1) Normalizar a média e variância alvo para o intervalo [0, 1]. (2) Validar a condição de viabilidade ($\sigma_X^2 < \mu_X(1-\mu_X)$). (3) Calcular diretamente os parâmetros de forma $\alpha$ e $\beta$. (4) Gerar amostras e re-escalar para o intervalo `[V_MIN, V_MAX]`.

3.  **Módulo para CV Alto (`samplers/mixture_beta.py`):**
    * **Lógica:** Implementará o modelo de mistura bimodal simétrica para atingir alta variância.
    * **Passos:** (1) Fixar o peso da mistura `w = 0.5` e a variância dos componentes $\sigma_c$. (2) Calcular a separação `d` entre as médias dos componentes necessária para atingir a variância alvo. (3) Calcular as médias dos dois componentes ($\mu_1, \mu_2$). (4) Para cada componente, usar a lógica do `beta_4p.py` para encontrar seus parâmetros de forma `(α_i, β_i)`. (5) Gerar e combinar as amostras.

**Justificativa da Escolha:**
Esta nova arquitetura é superior à anterior por três razões principais:
* **Fundamentação Teórica:** Substitui uma heurística de correção (`Normal-clip-correção`) por métodos analíticos e estatisticamente sólidos, diretamente recomendados pela literatura de referência (e.g., Devroye, 1986).
* **Robustez e Precisão:** A solução analítica do Beta e a calibração da mistura bimodal garantem que o CV alvo será atingido com alta precisão, eliminando os warnings de "falha de convergência" que vimos nos pilotos.
* **Modularidade:** A separação da lógica em módulos distintos (`beta_4p.py`, `mixture_beta.py`) e um dispatcher torna o código mais limpo, mais fácil de testar e de manter.

**Próximos Passos Imediatos:**
1.  Criar a branch `dev`.
2.  Criar o novo subdiretório `src/generator/samplers/`.
3.  Implementar os novos módulos `beta_4p.py` e `mixture_beta.py`.
4.  Refatorar `src/generator/cli.py` para que a função `generate_velocities` atue como o dispatcher.
5.  Atualizar a suíte de testes `tests/test_generator.py` para validar os novos módulos.

**Assunto:** Consolidação da Arquitetura Final do Gerador (Protocolos v6.0 e v6.1) com Base em Revisão Bibliográfica.

**Contexto:**
Após a conclusão da pesquisa bibliográfica sobre Geração de Grafos (Tema 1) e Cálculo de Modularidade (Tema 3), foram tomadas decisões de engenharia para refatorar e blindar o módulo gerador (`src/generator/`), alinhando-o com as melhores práticas do estado da arte.

**1. Decisão: Adoção de Estratégia Híbrida para Geração de Grafos (Protocolo v6.0)**

* [cite_start]**Análise:** A literatura [cite: 1019] confirmou que a melhor metodologia para gerar grafos conexos depende da densidade alvo. [cite_start]O método construtivo (árvore + arestas) é ideal para grafos esparsos, enquanto a amostragem por rejeição é superior para grafos densos [cite: 1121, 1182-1183].
* **Decisão:** O `build_edge_list` será refatorado para atuar como um **dispatcher**. [cite_start]Ele calculará o limiar de conectividade de Erdős-Rényi ($m_{crit} \approx 2n\log n$) [cite: 1131, 1183] e selecionará dinamicamente o algoritmo:
    * **Se `m_alvo > m_crit` (Denso):** Usará um novo método de **amostragem por rejeição**.
    * **Se `m_alvo <= m_crit` (Esparso):** Usará o método **construtivo** já implementado.
* [cite_start]**Justificativa:** Esta abordagem garante a máxima performance computacional para todos os cenários, evitando os piores casos de cada método (rejeição em grafos esparsos, complexidade desnecessária em grafos densos)[cite: 1185].

**3. Decisão: Arquitetura Modular para Cálculo de Modularidade (Protocolo v6.1)**

* **Análise:** O cálculo de modularidade é uma funcionalidade complexa e computacionalmente pesada. [cite_start]A literatura confirma que o algoritmo Greedy (CNM) é determinístico, mas mais lento, enquanto o Louvain é mais rápido, mas não-determinístico e melhor para grafos grandes[cite: 1439, 1446, 1448].
* **Decisão:** A lógica de cálculo de modularidade será **encapsulada em um novo sub-pacote (`src/generator/community/`)**. Este pacote conterá:
    * Um **dispatcher** que escolhe entre o `greedy_modularity_communities` (para grafos com $|E| \le 2M$) e o `community_louvain` (para grafos maiores).
    * O cálculo será condicional e o schema (`v1.1`) permitirá o valor `null` para o campo `modularity`.
    * A dependência `python-louvain` será declarada como **opcional** no `pyproject.toml` para minimizar a pegada de dependências do framework base.
* **Justificativa:** Esta abordagem isola uma preocupação complexa, otimiza a performance escolhendo o melhor algoritmo para cada escala, e mantém o core do gerador leve, seguindo princípios de design de software robustos.

**Status Final:**
Com estas decisões, o design teórico do gerador de instâncias está **completo e congelado**. O plano de implementação está claro.


## 2025-07-28

**Assunto:** Conclusão da Pesquisa Teórica e Consolidação da Metodologia.

- **Marco:** Análise dos relatórios de pesquisa bibliográfica concluída.
- **Decisão:** A metodologia completa do projeto, incluindo a arquitetura do gerador híbrido (Wilson/Rejeição para grafos, Beta/Bimodal para velocidades) e da análise de modularidade (Greedy condicional), foi consolidada.
- **Resultado:** A tese do projeto está agora fortemente embasada na literatura sobre "No Free Lunch Theorems", Análise da Paisagem de Fitness e algoritmos de otimização.
- **Documento Mestre:** Todas as decisões e suas justificativas teóricas foram centralizadas no novo documento de design: `docs/decisions/003_metodologia_gerador_e_analise.md`.
- **Status:** Fase 0 (Configuração e Design) oficialmente concluída.

**Assunto:** Definição do Plano de Trabalho para o Desenvolvimento Paralelo das Fases 1 e 2.

- **Marco:** O plano de trabalho completo, que detalha a estratégia de implementação desacoplada das Fases 1 (Heurísticas) e 2 (Simulação), foi finalizado.
- **Decisão:** A comunicação entre as duas frentes será feita via um **contrato de dados formal** (`solution.csv`), validado por schema.
- **Documento Mestre:** O plano completo foi registrado no novo documento `docs/01_project_plan_and_workflow.md`.
- **Status:** A fase de planejamento está concluída. O desenvolvimento pode começar em ambas as frentes de forma independente.
