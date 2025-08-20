### 1. Filosofia e Escopo da Pesquisa

* **Decisão:** O projeto focará na **Fase 1**, uma caracterização de performance de heurísticas em ambiente controlado, para construir um **Modelo Preditivo de Performance (MPP)**.
* **Opções Excluídas:**
    * Focar apenas em "encontrar a melhor heurística".
    * Iniciar com um ambiente caótico e com ruído ("aleatoriedade imprevista").
* **Justificativa:** A abordagem de "encontrar o melhor" é simplista. A tese mais forte e cientificamente mais valiosa é **entender *quando* e *por que*** cada heurística performa bem. Para isso, precisamos primeiro estabelecer uma **validade interna** em um ambiente controlado para isolar as variáveis. A introdução de ruído (Fase 2) só é metodologicamente correta após termos essa linha de base bem definida.

### 2. Arquitetura Técnica e Fluxo de Trabalho

* **Decisão:** Adotamos uma arquitetura de **duas máquinas** com controle remoto. O desenvolvimento ocorre em um notebook (Windows 11 + WSL2) e a execução massiva em um desktop fixo (Windows 10 + **WSL1**). O controle é feito via **SSH na porta 2222** para o ambiente WSL1 do desktop.
* **Opções Excluídas:**
    * Docker/Hyper-V/VirtualBox no desktop (inviabilizado por falta de virtualização de hardware).
    * Execução nativa no Windows (reprodutibilidade muito baixa).
    * Execução via `wsl.exe` (frágil e complexo).
    * SSH para o host Windows (conflito de portas com o SSH do WSL1).
* **Justificativa:** A falta de virtualização no desktop foi a restrição crítica. A solução com **WSL1** foi escolhida como o melhor equilíbrio, pois oferece um ambiente Linux quase idêntico ao de desenvolvimento (alta reprodutibilidade) sem a complexidade e o risco de um dual-boot. A conexão SSH direta ao WSL1 em uma porta não-padrão (`2222`) é uma solução de engenharia padrão, mais robusta e limpa do que workarounds.

* **Decisão:** A implementação das heurísticas da Fase 1 será feita **inteiramente em Python**.
* **Opções Excluídas:**
    * Implementar as heurísticas em C++ para performance.
* **Justificativa:** O gargalo do projeto nesta fase é a **velocidade de desenvolvimento e descoberta**, não o tempo de CPU. A complexidade de implementar e criar bindings para sete meta-heurísticas em C++ introduziria um risco e um atraso inaceitáveis. A otimização em C++ foi relegada como uma possibilidade para a Fase 2, a ser aplicada apenas nos algoritmos que se provarem "campeões".

### 3. Geração de Dados e Contrato

* **Decisão:** O gerador (`src/generator/cli.py`) usa uma metodologia construtiva para garantir as propriedades do grafo.
    1.  **Conectividade:** É garantida pela criação de uma **árvore geradora aleatória** (`nx.random_labeled_tree`) como base, seguida pela adição de arestas de forma iterativa e performática para atingir a densidade alvo.
    2.  **Distribuição de Velocidade (CV):** Utiliza uma **distribuição Beta reescalada** com média móvel, com um **fallback para um método bimodal calibrado**, para garantir a geração de qualquer CV alvo de forma robusta.
* **Opções Excluídas:**
    * Geração G(n,p) simples (não garantia conectividade em baixas densidades).
    * Extração do componente gigante (alterava o número de nós, uma variável de controle).
    * Geração de velocidades via "Normal + Clip" (imprecisa).
    * Lógica de geração de grafos com complexidade `O(n²)`.
    * Gerador baseado em Ruído Perlin (introduzia variáveis de confusão).
* **Justificativa:** As decisões foram tomadas para maximizar o **controle sobre as variáveis independentes** do experimento. O gerador final garante, por design, que uma instância com `N` nós e densidade `p` seja conexa e tenha os parâmetros estatísticos solicitados, eliminando fontes de viés e garantindo a validade do dataset.

* **Decisão:** O formato de dados de entrada e saída é um **JSON único**, validado por um **schema formal** (`specs/schema_input.json`).
* **Opções Excluídas:**
    * Múltiplos arquivos de saída (`.npy`, `.txt`, `.pkl`).
    * Parse de arquivos de texto de formato livre.
* **Justificativa:** Um contrato de dados rigoroso e validado por schema é a base para um pipeline automatizado robusto. Ele previne erros de formato e garante que todos os componentes do sistema (gerador, heurísticas, analisador) "falem a mesma língua".

### 4. Qualidade, Automação e Documentação

* **Decisão:** O projeto utiliza **Poetry** para gerenciamento de dependências, **`pre-commit` com `ruff` e `black`** para qualidade de código, e **GitHub Actions** para Integração Contínua (CI).
* **Opções Excluídas:**
    * `requirements.txt` (menos robusto).
    * Verificação de qualidade manual.
* **Justificativa:** Esta tríade de ferramentas automatiza a consistência do ambiente, do estilo de código e dos testes, garantindo um alto nível de qualidade e reprodutibilidade com esforço mínimo após a configuração inicial.

* **Decisão:** A documentação segue um **sistema de três camadas**: um `LOG.md` informal para o diário de bordo, relatórios técnicos formais em `docs/reports/` para marcos concluídos, e Notebooks Jupyter para a análise reprodutível.
* **Opções Excluídas:**
    * Deixar toda a escrita para o final.
* **Justificativa:** Este método transforma a escrita de um evento único e massivo em um processo contínuo e gerenciável. Ele captura o **racional** por trás das decisões (no `LOG.md`) e constrói o artigo final de forma incremental, garantindo maior qualidade e menos estresse.
