# ==============================================================================
# Estágio 1: Builder - Instala as dependências
# ==============================================================================
FROM python:3.11-slim AS builder

# Define variáveis de ambiente para o Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONUNBUFFERED=1

# Instala o Poetry
RUN pip install poetry

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia apenas os arquivos de dependência para aproveitar o cache do Docker
COPY pyproject.toml poetry.lock ./

# Instala apenas as dependências de produção (ignora `pytest`, `ruff`, etc.)
# A instalação acontece aqui, no ambiente de build
# CORREÇÃO: Usando a flag moderna `--without dev`
RUN poetry install --without dev --no-root

# ==============================================================================
# Estágio 2: Final - Cria a imagem de produção limpa
# ==============================================================================
FROM python:3.11-slim AS final

# Define o diretório de trabalho
WORKDIR /app

# Copia as dependências já instaladas do estágio 'builder' para a /app
# (Poetry as instala em /app/ por padrão com a config que usamos)
COPY --from=builder /app/ /app/

# Copia o código-fonte do projeto
COPY src/ ./src

# Define o ponto de entrada padrão do container.
# Quando o container rodar, ele executará o CLI principal do seu framework.
ENTRYPOINT ["python", "-m", "src.hpc_framework.cli"]
