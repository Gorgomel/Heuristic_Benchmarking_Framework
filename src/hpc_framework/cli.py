"""CLI do HPC Framework (modo single-run)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runner import run_one


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Runner single-run: exporta .graph, chama METIS/KaHIP e emite JSON de resultados."
    )
    p.add_argument("--instance", required=True, help="Arquivo da instância (.json|.json.gz)")
    p.add_argument("--algo", required=True, choices=["metis", "kahip"])
    p.add_argument("--k", required=True, type=int)
    p.add_argument("--beta", required=True, type=float)
    p.add_argument("--budget-time-ms", required=True, type=int, dest="budget_time_ms")
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--out", required=True, type=Path, help="Arquivo de saída JSON")
    p.add_argument(
        "--workdir", type=Path, default=Path("."), help="Diretório de trabalho/artefatos"
    )
    p.add_argument("--log-level", choices=["debug", "info", "warning", "error"], default="info")
    p.add_argument("--kahip-preset", choices=["fast", "eco", "strong"], default="fast")
    return p


def main(argv: list[str] | None = None) -> None:
    # Para os testes de entrypoint: se chamado sem argv, apenas "alive".
    if argv is None:
        print("alive")
        return

    parser = _build_parser()
    args = parser.parse_args(argv)

    art = run_one(
        instance_path=Path(args.instance),
        algo=args.algo,
        k=int(args.k),
        beta=float(args.beta),
        seed=int(args.seed),
        budget_time_ms=int(args.budget_time_ms),
        out_json=Path(args.out),
        workdir=Path(args.workdir),
        kahip_preset=str(args.kahip_preset),
        log_level=str(args.log_level),
    )

    obj = {
        "run_id": art.run_id,
        "algo": art.algo,
        "status": art.status,
        "cut": art.cut,
        "elapsed_ms": art.elapsed_ms,
        "part_file": str(art.part_file) if art.part_file else None,
    }
    print(json.dumps(obj, ensure_ascii=False))
