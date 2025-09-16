# ADR 004 — Estratégia de Testes, Coverage e CI

**Status**: Proposto • **Data**: 2025-09-XX

## Contexto
O projeto entrou em fase de consolidação do gerador e do protocolo experimental.
Precisamos garantir regressão mínima, documentação navegável e build reproduzível.

## Decisão
- Adotar **pytest + pytest-cov** com limiar inicial de 75%.
- Padronizar **docstrings estilo Google** e publicar API com **MkDocs + mkdocstrings**.
- Rodar **CI (GitHub Actions)** com linters (ruff), format (black --check), testes e build do site.
- Manter **rastreabilidade** teste ↔ requisito em `docs/testing/TRACEABILITY.md`.

## Consequências
- Atrito inicial baixo; ganho alto em visibilidade de falhas.
- Rever gradualmente o limiar de cobertura.
- Incentivo a docstrings e `type hints` para API legível.
