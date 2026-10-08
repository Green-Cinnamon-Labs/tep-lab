"""
run_timeline.py — linha do tempo de uma rodada gravada pelo `local/scripts/record_run.py`.

Um gráfico com quatro painéis, todos no tempo simulado da planta (`clock.t_h`):

1. custo J contra o orçamento (`maxCost`) da política;
2. as conditions do veredito como faixas (verde True, vermelho False, cinza Unknown);
3. o Predictability Index de cada malha contra o limiar (`--pi-threshold`); pontos vazados são
   avaliações em que a malha não foi julgada (abaixo do portão ou sem índice);
4. o σ da válvula de cada malha contra o portão de variabilidade (`--gate`), em escala log.

Marcos (`--mark 3.21:"IDV6 ligado"`) viram linhas verticais em todos os painéis — use para o instante
em que um distúrbio foi ligado e desligado.

Uso (de dentro de tep-lab/analysis):
    poetry run run-timeline ../data/experiment_82/idv6_2026-10-08.csv \\
        --mark 3.21:"IDV6 ligado" --mark 10.3:"IDV6 desligado"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

CONDITIONS = ["PolicyCompliant", "CostWithinBudget", "TargetsMet", "ConstraintsSatisfied", "ControlLoopsHealthy"]
CONDITION_COLOR = {"True": "#4caf50", "False": "#ef5350", "Unknown": "#9e9e9e"}


def load(path: Path) -> pd.DataFrame:
    """Uma linha por avaliação do supervisor (a gravação pode repetir a mesma avaliação)."""
    df = pd.read_csv(path)
    key = df["last_evaluation_time"].fillna(df["wall_time"])
    df = df.loc[~key.duplicated()].copy()
    df = df.dropna(subset=["sim_t_h"]).sort_values("sim_t_h")
    for c in CONDITIONS:
        if c in df:
            df[c] = df[c].astype(str).where(df[c].notna(), "Unknown")
    return df


def loop_names(df: pd.DataFrame) -> list[str]:
    return sorted({c[: -len(".pi")] for c in df.columns if c.endswith(".pi")})


def parse_mark(text: str) -> tuple[float, str]:
    t, _, label = text.partition(":")
    return float(t), label or t


def plot(df: pd.DataFrame, out: Path, pi_threshold: float, gate: float, marks: list[tuple[float, str]], title: str) -> None:
    loops = loop_names(df)
    t = df["sim_t_h"]
    fig, axes = plt.subplots(4, 1, figsize=(12, 11), sharex=True, gridspec_kw={"height_ratios": [3, 1.6, 3, 2]})
    ax_j, ax_c, ax_pi, ax_sd = axes

    # 1. J
    ax_j.plot(t, df["cost"], color="#1f77b4", lw=1.6, label="J")
    if df["max_cost"].notna().any():
        ax_j.plot(t, df["max_cost"], color="#ef5350", ls="--", lw=1.2, label="maxCost")
    unit = df["cost_unit"].dropna().iloc[0] if df["cost_unit"].notna().any() else ""
    ax_j.set_ylabel(f"J ({unit})")
    ax_j.legend(loc="upper left", fontsize=8)
    ax_j.grid(alpha=0.3)

    # 2. conditions como faixas
    # cada faixa vai até a avaliação seguinte (a última, até o passo mediano)
    step = t.diff().median() if len(t) > 1 else 0.01
    widths = (t.shift(-1) - t).fillna(step)
    for i, c in enumerate([c for c in CONDITIONS if c in df]):
        for ti, w, v in zip(t, widths, df[c]):
            ax_c.broken_barh([(ti, w)], (i - 0.4, 0.8), color=CONDITION_COLOR.get(v, "#9e9e9e"))
    names = [c for c in CONDITIONS if c in df]
    ax_c.set_yticks(range(len(names)), names, fontsize=8)
    ax_c.set_ylim(-0.6, len(names) - 0.4)

    # 3. PI por malha
    for name in loops:
        judged = df[f"{name}.evaluated"].astype(str) == "True"
        line = ax_pi.plot(t, df[f"{name}.pi"], lw=1.0, alpha=0.6, label=name)[0]
        ax_pi.scatter(t[judged], df.loc[judged, f"{name}.pi"], s=14, color=line.get_color())
        ax_pi.scatter(t[~judged], df.loc[~judged, f"{name}.pi"], s=14, facecolors="none", edgecolors=line.get_color())
    ax_pi.axhline(pi_threshold, color="#ef5350", ls="--", lw=1.2, label=f"minPredictability {pi_threshold:g}")
    ax_pi.set_ylabel("Predictability Index")
    ax_pi.set_ylim(0, 1)
    ax_pi.legend(loc="upper left", fontsize=8, ncol=2)
    ax_pi.grid(alpha=0.3)

    # 4. σ da válvula
    for name in loops:
        ax_sd.plot(t, df[f"{name}.output_std"], lw=1.2, label=name)
    ax_sd.axhline(gate, color="#ef5350", ls="--", lw=1.2, label=f"minOutputStd {gate:g}")
    ax_sd.set_yscale("log")
    ax_sd.set_ylabel("σ da válvula (%)")
    ax_sd.set_xlabel("tempo simulado — clock.t_h (h)")
    ax_sd.legend(loc="center right", fontsize=8, ncol=2)
    ax_sd.grid(alpha=0.3, which="both")

    for tm, label in marks:
        for ax in axes:
            ax.axvline(tm, color="#ff9800", lw=1.4)
        ax_j.annotate(label, (tm, 1.0), xycoords=("data", "axes fraction"), xytext=(3, -12),
                      textcoords="offset points", fontsize=9, color="#e65100")

    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print(f"[run-timeline] {len(df)} avaliações → {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Linha do tempo de uma rodada gravada pelo record_run.py")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, help="PNG de saída (default: ao lado do CSV, mesmo nome)")
    ap.add_argument("--pi-threshold", type=float, default=0.12, help="minPredictability da política (default 0.12)")
    ap.add_argument("--gate", type=float, default=0.05, help="minOutputStd da política, em %% (default 0.05)")
    ap.add_argument("--mark", action="append", default=[], metavar="T:ROTULO",
                    help="marco vertical em clock.t_h, ex. 3.21:\"IDV6 ligado\" (pode repetir)")
    ap.add_argument("--title", default=None)
    args = ap.parse_args()

    out = args.out or args.csv.with_suffix(".png")
    plot(load(args.csv), out, args.pi_threshold, args.gate, [parse_mark(m) for m in args.mark],
         args.title or args.csv.stem)


if __name__ == "__main__":
    main()
