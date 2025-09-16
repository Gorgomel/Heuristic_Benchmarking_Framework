#!/usr/bin/env bash
set -euo pipefail
echo "### SYSTEM"
uname -a
lsb_release -a || cat /etc/os-release
echo "### CPU & MEM"
lscpu | egrep 'Model name|CPU\(s\)|Thread|Flags' || true
free -h || true
echo "### PYTHON & POETRY"
python3 -V
poetry --version || true
echo "### PYTHON PKGS"
poetry run python -c "import sys,platform; print(sys.version); print(platform.platform())" || true
poetry run python -c "import numpy,pandas,scipy; print('numpy',numpy.__version__,'pandas',pandas.__version__,'scipy',scipy.__version__)" || true
echo "### METIS/KaHIP"
for b in gpmetis ndmetis mpmetis kaffpa kaffpaE parhip; do
  if command -v "$b" >/dev/null 2>&1; then
    p="$(command -v "$b")"; real="$(readlink -f "$p" || echo "$p")"
    echo "BIN=$b PATH=$real"
    dpkg -S "$real" 2>/dev/null | head -n1 || true
    dpkg -s metis 2>/dev/null | grep -E '^Version|^Architecture' || true
    "$b" --help 2>&1 | head -n 2 || true
  else
    echo "BIN=$b (not found)"
  fi
done
echo "### LOGGING SNAPSHOT"
poetry run python - <<'PY' || true
import logging
root = logging.getLogger()
print("Root level:", logging.getLevelName(root.level))
print("Root handlers:", [type(h).__name__ for h in root.handlers])
log = logging.getLogger("hpc_framework")
print("HPC level:", logging.getLevelName(log.level))
print("HPC handlers:", [type(h).__name__ for h in log.handlers])
PY

#bash tools/diagnostics.sh > data/system_report.txt
