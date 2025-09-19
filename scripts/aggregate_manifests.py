#!/usr/bin/env python
"""Aggregate multiple v1 manifests into a flat CSV (one row per manifest)."""

from __future__ import annotations

import argparse
import csv
import glob
import json
from pathlib import Path
from typing import Any

# Colunas padrão (você pode ampliar sem quebrar nada)
FIELDS = [
    "timestamp",
    "instance_id",
    "algo",
    "k",
    "beta",
    "seed",
    "budget_time_ms",
    "status",
    "returncode",
    "elapsed_ms",
    "metrics.cutsize_best",
    "metrics.imbalance_raw",
    "paths.workdir",
    "paths.graph_path",
    "paths.part_path",
    # Extras úteis (não-obrigatórios no schema)
    "env.python",
    "env.os",
    "env.os_release",
    "env.cpu.model",
    "env.cpu.cores_logical",
    "env.cpu.cores_physical",
    "env.cpu.freq_mhz",
    "tools.gpmetis.exists",
    "tools.gpmetis.version",
    "tools.kaffpa.exists",
    "tools.kaffpa.version",
]


def _get(d: dict[str, Any], dotted: str) -> Any:
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def main() -> None:
    ap = argparse.ArgumentParser(description="Aggregate v1 manifests into CSV")
    ap.add_argument(
        "--in-glob", required=True, help='Glob for *.v1.json (e.g. "data/results_raw/*.v1.json")'
    )
    ap.add_argument("--out", required=True, help="Output CSV path")
    # opcional: permitir adicionar colunas extras via linha de comando
    ap.add_argument("--extra-fields", default="", help="Comma-separated dotted fields to append")
    args = ap.parse_args()

    files = sorted(glob.glob(args.in_glob))
    if not files:
        raise SystemExit(f"No files matched: {args.in_glob}")

    fields = list(FIELDS)
    if args.extra_fields.strip():
        for col in [c.strip() for c in args.extra_fields.split(",") if c.strip()]:
            if col not in fields:
                fields.append(col)

    rows: list[dict[str, Any]] = []
    for f in files:
        try:
            obj = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception as ex:
            print(f"[WARN] skipping {f}: {ex}")
            continue
        row = {field: _get(obj, field) for field in fields}
        row["_file"] = f
        rows.append(row)

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=["_file"] + fields)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {outp} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
