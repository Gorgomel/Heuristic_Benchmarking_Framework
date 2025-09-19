# scripts/run_phase_1.sh
#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
PLAN="${1:-"$ROOT/configs/plan_phase_1.yaml"}"

# valida plano
if [[ ! -f "$PLAN" ]]; then
  echo "erro: plano não encontrado: $PLAN" >&2
  exit 1
fi

# alinhar com o runner (evita variações por BLAS/threads)
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

need() { command -v "$1" >/dev/null 2>&1; }

# dependências externas (obrigatória/optativa)
if ! need gpmetis; then
  echo "erro: 'gpmetis' não está no PATH (METIS é obrigatório para o plano atual)." >&2
  exit 2
fi
if ! need kaffpa; then
  echo "aviso: 'kaffpa' não está no PATH (KaHIP será ignorado se o plano permitir)."
fi

run_cli() {
  # 1) Usar Poetry se existir no projeto
  if command -v poetry >/dev/null 2>&1 && [[ -f "$ROOT/pyproject.toml" ]]; then
    exec poetry run python -m hpc_framework.cli run --plan "$PLAN"
  fi

  # 2) Se o pacote já estiver disponível no Python do sistema
  if python3 - <<'PY' 2>/dev/null
import importlib.util, sys
sys.exit(0 if importlib.util.find_spec("hpc_framework") else 1)
PY
  then
    exec python3 -m hpc_framework.cli run --plan "$PLAN"
  fi

  # 3) Bootstrap: criar .venv local e instalar
  echo "Instalando em .venv local (pip)…"
  python3 -m venv "$ROOT/.venv"
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
  python -m pip install -U pip
  pip install .
  exec python -m hpc_framework.cli run --plan "$PLAN"
}

echo "Plano: $PLAN"
echo "Raiz:  $ROOT"
run_cli
