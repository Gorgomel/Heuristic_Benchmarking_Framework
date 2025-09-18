#!/usr/bin/env python
"""Paired comparison of cutsize (Wilcoxon + bootstrap CI) between two algorithms."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# SciPy é opcional: usa se existir, senão cai para teste de sinais
try:
    from scipy.stats import wilcoxon as _wilcoxon  # type: ignore

    _HAVE_SCIPY = True
except Exception:
    _HAVE_SCIPY = False
    _wilcoxon = None  # type: ignore[assignment]

PairKey = tuple[str, int, float, int]  # (instance_id, k, beta, seed)


def load(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def collect(files: list[Path]) -> pd.DataFrame:
    rows = []
    for f in files:
        try:
            o = load(f)
        except Exception as ex:
            print(f"[WARN] skipping {f}: {ex}")
            continue
        m = o.get("metrics", {}) if isinstance(o.get("metrics"), dict) else {}
        rows.append(
            {
                "file": str(f),
                "instance_id": o.get("instance_id", ""),
                "algo": o.get("algo", ""),
                "k": o.get("k", None),
                "beta": o.get("beta", None),
                "seed": o.get("seed", None),
                "status": o.get("status", ""),
                "cut": m.get("cutsize_best"),
                "elapsed_ms": o.get("elapsed_ms", None),
            }
        )
    return pd.DataFrame(rows)


def paired(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    df = df.dropna(subset=["cut"])
    df = df[df["status"] == "ok"]
    df["key"] = list(zip(df["instance_id"], df["k"], df["beta"], df["seed"], strict=False))
    A = df[df["algo"] == a].set_index("key")["cut"]
    B = df[df["algo"] == b].set_index("key")["cut"]
    common = sorted(set(A.index).intersection(B.index))
    return pd.DataFrame({"cut_a": A.loc[common], "cut_b": B.loc[common]}).reset_index()


def bootstrap_ci_median(
    x: np.ndarray, n_boot: int = 5000, alpha: float = 0.05
) -> tuple[float, float, float]:
    rng = np.random.default_rng(123)
    if x.size == 0:
        return float("nan"), float("nan"), float("nan")
    boot = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        s = rng.choice(x, size=x.size, replace=True)
        boot[i] = float(np.median(s))
    lo = np.percentile(boot, 100 * (alpha / 2))
    hi = np.percentile(boot, 100 * (1 - alpha / 2))
    return float(np.median(x)), float(lo), float(hi)


def _sign_test_p(diff: np.ndarray) -> float:
    """Fallback simples ao Wilcoxon: teste de sinais bilateral."""
    wins_b = int(np.sum(diff < 0))
    wins_a = int(np.sum(diff > 0))
    n = wins_a + wins_b
    if n == 0:
        return 1.0
    # aproximação normal (p=0.5), bilateral
    from math import erf, sqrt

    z = (wins_b - 0.5 * n) / (0.5 * (n**0.5))

    def _phi(z_):
        return 0.5 * (1.0 + erf(z_ / sqrt(2.0)))

    p_one = 1.0 - _phi(abs(z))
    return 2.0 * p_one


def main():
    ap = argparse.ArgumentParser(
        description="Comparação pareada (cutsize) entre dois algoritmos (Wilcoxon ou teste de sinais + bootstrap)"
    )
    ap.add_argument(
        "--in-glob",
        default="data/results_raw/*.v1.json",
        help='Glob de entrada (ex: "data/results_raw/*.v1.json")',
    )
    ap.add_argument("--a", default="metis", help="algoritmo A (baseline)")
    ap.add_argument("--b", default="kahip", help="algoritmo B (comparado)")
    ap.add_argument(
        "--out-md", default="data/results_raw/stats_compare.md", help="relatório markdown"
    )
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--min-pairs", type=int, default=5, help="mínimo de pares para análise robusta")
    args = ap.parse_args()

    files = sorted(Path().glob(args.in_glob))
    if not files:
        print(f"Nenhum arquivo encontrado no padrão: {args.in_glob}")
        return

    df = collect(files)
    pairs = paired(df, args.a, args.b)
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    if pairs.empty:
        msg = "Sem pares comuns (mesma instância/k/beta/seed) para comparar."
        print(msg)
        out_md.write_text(f"# {args.a} vs {args.b}\n\n> {msg}\n", encoding="utf-8")
        return

    diffs = pairs["cut_b"].to_numpy(dtype=float) - pairs["cut_a"].to_numpy(
        dtype=float
    )  # <0 => B melhor
    n_pairs = diffs.size

    # Estatísticas simples
    mean_diff = float(np.mean(diffs))
    median_diff, lo_med, hi_med = bootstrap_ci_median(diffs, n_boot=5000, alpha=args.alpha)
    win_b = float(np.mean(diffs < 0.0))
    win_a = float(np.mean(diffs > 0.0))
    ties = float(np.mean(diffs == 0.0))

    # Teste de hipótese
    if _HAVE_SCIPY and n_pairs >= 1 and np.any(diffs != 0):
        stat, p = _wilcoxon(
            diffs, zero_method="wilcox", alternative="two-sided", correction=False, mode="auto"
        )  # type: ignore[misc]
        test_line = f"Wilcoxon: statistic={float(stat):.3f}, p-value={float(p):.3g}"
    else:
        p = _sign_test_p(diffs)
        test_line = f"Teste de sinais (fallback): p≈{p:.4f}"

    lines: list[str] = []
    lines.append(f"# Comparação {args.a} vs {args.b}")
    lines.append("")
    lines.append(f"- Pares válidos (status=ok): **{n_pairs}**")
    if n_pairs < args.min_pairs:
        lines.append(f"> ⚠️ Apenas {n_pairs} pares — gere mais runs pareados para robustez.")
        lines.append("")
    lines.append(f"- Diferença média (B − A): {mean_diff:.3f}")
    lines.append(
        f"- Mediana(Δ cut): {median_diff:.3f}  (IC{int((1 - args.alpha) * 100)}%: {lo_med:.3f}, {hi_med:.3f})"
    )
    lines.append(f"- {test_line}")
    lines.append(
        f"- Win-rate B (<0): {win_b * 100:.1f}% | Win-rate A (>0): {win_a * 100:.1f}% | Empates: {ties * 100:.1f}%"
    )
    lines.append("")
    concl = "indefinido"
    if hi_med < 0:
        concl = f"{args.b} melhor (IC da mediana < 0)"
    elif lo_med > 0:
        concl = f"{args.a} melhor (IC da mediana > 0)"
    lines.append(f"> **Conclusão:** {concl}.")
    lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWrote {out_md}")


if __name__ == "__main__":
    main()
