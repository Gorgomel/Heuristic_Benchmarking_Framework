"""Pack a runner JSON produced by the CLI into a v1 manifest (draft-07 schema)."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hpc_framework.runner import _env_snapshot, _tool_version, _which

try:
    from hpc_framework.solvers.common import (  # type: ignore
        beta_to_kahip_imbalance,
        beta_to_metis_ufactor,
    )
except Exception:

    def beta_to_metis_ufactor(beta: float) -> int:  # fallback
        return int(round(beta * 1000))

    def beta_to_kahip_imbalance(beta: float) -> float:  # fallback
        return float(beta * 100.0)


def _load(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(
        description="Empacota JSON do runner em manifest v1 (schema draft-07)"
    )
    ap.add_argument("--in", dest="in_path", required=True, help="JSON produzido pelo runner")
    ap.add_argument("--out", dest="out_path", required=True, help="Destino do manifest v1")
    args = ap.parse_args()

    src = Path(args.in_path)
    dst = Path(args.out_path)

    obj = _load(src)

    algo = str(obj.get("algo", ""))
    beta = float(obj.get("beta", 0.0))
    k = int(obj.get("k", 2))

    # imbalance_raw: depende do solver
    if algo == "metis":
        imb_raw: int | float | None = beta_to_metis_ufactor(beta)
    elif algo == "kahip":
        imb_raw = beta_to_kahip_imbalance(beta)
    else:
        imb_raw = None

    env = _env_snapshot()
    tools = {
        "gpmetis": {
            "exists": bool(_which("gpmetis")),
            "version": _tool_version(["gpmetis"]) if _which("gpmetis") else "",
        },
        "kaffpa": {
            "exists": bool(_which("kaffpa")),
            "version": _tool_version(["kaffpa"]) if _which("kaffpa") else "",
        },
    }

    manifest = {
        "timestamp": datetime.now(UTC).isoformat(),
        "instance_id": obj.get("instance_id", ""),
        "algo": algo,
        "k": k,
        "beta": beta,
        "seed": int(obj.get("seed", 0)),
        "budget_time_ms": int(obj.get("budget_time_ms", 0)),
        "status": obj.get("status", "error"),
        "returncode": obj.get("returncode"),
        "elapsed_ms": int(obj.get("elapsed_ms", 0)),
        "stdout": obj.get("stdout", ""),
        "stderr": obj.get("stderr", ""),
        "metrics": {
            "cutsize_best": obj.get("cutsize_best"),
            "n_nodes": None,  # pode preencher no futuro
            "balance_tolerance": beta,
            "imbalance_raw": imb_raw,
        },
        "env": env,
        "tools": tools,
        "paths": {
            "workdir": obj.get("workdir", ""),
            "graph_path": obj.get("graph_path", ""),
            "part_path": obj.get("part_path"),
        },
        # metadados do schema:
        "schema_version": "1.0.0",
        "schema_path": "specs/jsonschema/solver_run.schema.v1.json",
    }

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {dst}")


if __name__ == "__main__":
    main()
