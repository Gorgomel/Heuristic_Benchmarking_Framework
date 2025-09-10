# Guia de Testes

> Escopo inicial: **gerador de instâncias** (CLI, JSON-first, schema v1.1, políticas de modularidade e CV)
> Futuro próximo: runner/orquestrador, métricas, pipelines de campanha.

## Como executar localmente

```bash
poetry install --no-interaction
pytest -q
# testes mais lentos/opcionais
pytest -m "slow" -q
````

**Ambiente alvo:** Python 3.11. `PYTHONHASHSEED=0`. Não exigimos mono-thread de BLAS para unit tests.

## Padrões

* Seeds fixas em testes estocásticos.
* Artefatos em diretórios efêmeros (`tmp_path`), **sem** poluir `data/instances`.
* Estilo *Arrange–Act–Assert* / *Given–When–Then*.
* Mensagens de falha claras e parametrização (`@pytest.mark.parametrize`) quando couber.

## Marcadores

* `@pytest.mark.schema` — validações de schema/contrato.
* `@pytest.mark.cli` — invocação do CLI e parsing leve.
* `@pytest.mark.slow` — cenários maiores, ou smoke de desempenho.
* `@pytest.mark.docs` — verificação de exemplos do README/docs.

## O que é coberto agora

* JSON-first validado (schema v1.1).
* Gate de modularidade → `modularity: null` quando limite for excedido.
* Teto de CV (média no centro) = **1/3** com *warning* quando capado.
* Exemplos mínimos de CLI do README executam (smoke).

## O que entra em seguida

* Freeze de schemas versionados em `specs/1.1/...` e teste dedicado.
* Smoke de desempenho com limites suaves (sem quebrar CI).
* Testes do runner/orquestrador (quando estabilizar interface).

## Métricas de qualidade (indicativas)

* Cobertura prática 70–80% em `src/generator/*` (excluindo logs e trilhas de erro raras).
* Zero *flake* em testes determinísticos (se acontecer, registrar seed na mensagem do teste).

# Estratégia de Testes

## Escopo atual
- **Gerador**: validação de schema v1.1 (`specs/schema_input.json` e `specs/schema_output.json`),
  conectividade, densidade-alvo (tolerância), CV de velocidade (cap e warning), gate de modularidade.
- **Sanidade**: execução “fim-a-fim” em cenários curtos com persistência `.json`/`.json.gz`.

## Tipos de teste
- **Unitários** (`tests/test_generator.py`): funções utilitárias (bisseção de ε, amostragem,
  validações de campos), flags e caps.
- **Integração** (`tests/test_sanity.py`): CLI e JSON-first, do input ao output.
- **Regressão** (novos): “gate” de modularidade, CV perto do teto (cap), schema freeze.

## Como rodar
```bash
poetry run pytest -q
````

## Cobertura

* Alvo inicial: **75%** (subir gradualmente).
* Métrica: `pytest-cov` com relatórios `term-missing` e `xml` (para CI).

## Marcadores

* `@pytest.mark.schema` — casos que validam contratos.
* `@pytest.mark.cli` — execução via CLI.
* `@pytest.mark.slow` — testes pesados (opt-out por padrão).
* `@pytest.mark.docs` — exemplos do README/docs (evita bit rot).

````

`docs/testing/CI.md`
```markdown
# Integração Contínua (CI)

## Pipeline
1. **Instalação** via Poetry.
2. **Linters** (ruff) e formatação (black --check).
3. **Testes** com cobertura (pytest + pytest-cov).
4. **Artefatos**: `coverage.xml` e `site/` (build do MkDocs).
5. (Opcional) **Publicação** do site no GitHub Pages.

## Branches/Disparos
- `push`/`pull_request` para `main` e branches de release.
- Jobs rodam em Python 3.11.

## Falhas comuns
- Queda de cobertura abaixo do limiar.
- `ruff`/`black` acusando style.
- Docstrings ausentes em objetos expostos nas páginas de API.
