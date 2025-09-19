from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

SYNTH_DIR = Path("data/instances/synthetic")


def _read_json(path: Path) -> dict[str, Any]:
    if str(path).endswith(".gz"):
        with gzip.open(path, "rt") as f:
            return json.load(f)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _get_modularity(obj: dict[str, Any]) -> float | None:
    # tenta onde for comum: top-level "modularity", ou "metrics": { "modularity": ... }
    if "modularity" in obj:
        return obj["modularity"]
    if "metrics" in obj and isinstance(obj["metrics"], dict):
        return obj["metrics"].get("modularity", None)
    return None


def test_modularity_is_null_on_modnull_instances():
    """Regressão: qualquer instância 'modnull_*' deve manter modularidade nula/ausente.
    Isso cobre o gate (p.ex., 'min(1.2e6, 0.30·M)' ou política equivalente).
    """
    candidates = sorted(p for p in SYNTH_DIR.glob("modnull_*.json.gz"))
    assert candidates, "não há arquivos modnull_* no diretório sintético"

    for path in candidates:
        obj = _read_json(path)
        mod = _get_modularity(obj)
        assert mod is None, f"esperava modularidade nula em {path.name}, veio: {mod!r}"
