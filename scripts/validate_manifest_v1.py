#!/usr/bin/env python
"""Validate one or more v1 manifests against the JSON Schema (draft-07)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator


def _load_json(p: Path) -> Any:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as ex:
        print(f"[ERRO] Falha lendo JSON '{p}': {ex}", file=sys.stderr)
        sys.exit(2)


def _validate_one(schema: dict[str, Any], doc: dict[str, Any], name: str) -> tuple[bool, str]:
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
    if not errors:
        return True, f"[OK] {name}"
    lines = [f"[FAIL] {name} — {len(errors)} erro(s):"]
    for e in errors:
        path = ".".join([str(p) for p in e.path]) or "<root>"
        lines.append(f"  - path={path} :: {e.message}")
    return False, "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Valida manifest v1 contra schema draft-07")
    ap.add_argument("--schema", required=True, help="Caminho do schema JSON")
    ap.add_argument(
        "--in", dest="inputs", nargs="+", required=True, help="Arquivos .v1.json para validar"
    )
    args = ap.parse_args()

    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(f"[ERRO] Schema não encontrado: {schema_path}", file=sys.stderr)
        sys.exit(2)

    schema = _load_json(schema_path)

    any_fail = False
    for s in args.inputs:
        p = Path(s)
        if not p.exists():
            print(f"[ERRO] Arquivo não encontrado: {p}", file=sys.stderr)
            any_fail = True
            continue
        doc = _load_json(p)
        ok, msg = _validate_one(schema, doc, p.name)
        print(msg)
        any_fail = any_fail or (not ok)

    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
