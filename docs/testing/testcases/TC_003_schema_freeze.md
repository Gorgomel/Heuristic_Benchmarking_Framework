# TC_003 — Congelamento do Schema v1.1

**Objetivo**
Assegurar que os JSONs produzidos seguem o **schema v1.1** (inputs e/ou outputs), incluindo a aceitação explícita de `modularity: null`.

**Pré-condições**
- `jsonschema` instalado
- Schema carregado de `specs/schema_input.json` (ou de uma pasta versionada `specs/1.1/...` quando congelar)

**Passos**
1. Carregar o schema **exato** que o projeto declara como oficial (v1.1).
2. Validar o JSON gerado pelo CLI para um cenário básico.
3. Injetar `modularity: null` e validar novamente.

**Resultados esperados**
- Validação **aprovada** com `modularity: null`.
- Validação **aprovada** para campos obrigatórios mínimos documentados.

**Notas**
- Quando o schema for versionado em pastas (ex.: `specs/1.1/…`), atualizar o *loader* e este teste.
