"""
loop_rereading.py — releitura do Predictability Index na escala do artigo de Bradu et al.

O historian calcula `PI = 1 − σ²_r / mse` (`tep-historian/src/tep_historian/loop_performance.py`).
A leitura da monografia, baseada na fórmula e nos exemplos do artigo, é a contrária: erro previsível
deixa pouco resíduo e o índice fica baixo, `PI_artigo = σ²_r / mse`. Como o historian satura o
índice em [0, 1], `PI_artigo = 1 − PI` vale exatamente sempre que o índice gravado está entre 0 e 1.

Este script refaz, sobre gravações do `local/scripts/record_run.py`, o julgamento das malhas que o
supervisor teria feito na escala do artigo, com as mesmas regras de `plant-supervisor`
(`internal/evaluate/loops.go`), só que sem o critério de seguimento (`maxOffset`):

1. a malha só é julgada se o σ da válvula passar do portão (`--gate`, o `minOutputStd`);
2. uma malha julgada é ruim se `PI_artigo` ficar abaixo do limite;
3. `ControlLoopsHealthy` vira False quando há malha ruim em `--persistence` avaliações seguidas.

O limite vem da rodada nominal (`--nominal`): o maior múltiplo de 0,1 abaixo do menor `PI_artigo`
nominal menos `--margin` — a mesma ideia do 0,12 da política atual, posto abaixo do mínimo nominal
com folga. `--threshold` fixa o limite à mão.

Uso (de dentro de tep-lab/analysis):
    poetry run loop-rereading --nominal ../data/experiment_82/calibracao_2026-10-08.csv \\
        --run ../data/experiment_82/calibracao_2026-10-08.csv --label "Calibração" \\
        --run ../data/experiment_82/idv6_2026-10-08.csv --label "Exp 25" \\
        --mark 2:2.31:"IDV6 ligado" --out ../data/experiment_82/releitura.png
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .run_timeline import load, loop_names  # noqa: E402


@dataclass
class Replay:
    """O julgamento refeito de uma rodada."""

    label: str
    evaluations: int
    first_false: float | None  # clock.t_h em que ControlLoopsHealthy teria virado False
    flagged_at_first_false: list[str]
    first_bad: dict[str, float | None]  # primeira avaliação ruim de cada malha, sem persistência
    healthy: list[bool]  # ControlLoopsHealthy refeito, uma entrada por avaliação
    false_fraction: float  # fração das avaliações com ControlLoopsHealthy False


def article_scale(df: pd.DataFrame, name: str) -> pd.Series:
    return 1.0 - df[f"{name}.pi"]


def judged(df: pd.DataFrame, name: str, gate: float) -> pd.Series:
    return df[f"{name}.pi"].notna() & (df[f"{name}.output_std"] > gate)


def calibrate(nominal: pd.DataFrame, margin: float) -> tuple[float, float, float]:
    """Limite na escala do artigo a partir da rodada nominal: (limite, mínimo, máximo)."""
    values = pd.concat([article_scale(nominal, name) for name in loop_names(nominal)]).dropna()
    low, high = float(values.min()), float(values.max())
    return math.floor((low - margin) * 10) / 10, low, high


def replay(df: pd.DataFrame, label: str, threshold: float, gate: float, persistence: int) -> Replay:
    loops = loop_names(df)
    bad = {name: judged(df, name, gate) & (article_scale(df, name) < threshold) for name in loops}
    first_bad = {name: (float(df.loc[b, "sim_t_h"].iloc[0]) if b.any() else None) for name, b in bad.items()}
    # Como no supervisor: o contador de avaliações ruins seguidas volta a zero numa avaliação boa,
    # e a condition volta a True junto.
    streak, healthy, first_false, flagged_at_first = 0, [], None, []
    for i in range(len(df)):
        flagged = [name for name in loops if bad[name].iloc[i]]
        streak = streak + 1 if flagged else 0
        healthy.append(streak < persistence)
        if streak >= persistence and first_false is None:
            first_false, flagged_at_first = float(df["sim_t_h"].iloc[i]), flagged
    false_fraction = healthy.count(False) / len(healthy) if healthy else 0.0
    return Replay(label, len(df), first_false, flagged_at_first, first_bad, healthy, false_fraction)


def false_spans(t: pd.Series, healthy: list[bool]) -> list[tuple[float, float]]:
    """Trechos em que a condition refeita fica False; cada avaliação vale até a seguinte."""
    times = list(t)
    step = (times[-1] - times[0]) / max(len(times) - 1, 1)
    spans, start = [], None
    for i, ok in enumerate(healthy):
        if not ok and start is None:
            start = times[i]
        if ok and start is not None:
            spans.append((start, times[i]))
            start = None
    if start is not None:
        spans.append((start, times[-1] + step))
    return spans


def parse_mark(text: str) -> tuple[int, float, str]:
    index, _, rest = text.partition(":")
    t, _, label = rest.partition(":")
    return int(index), float(t), label or t


def plot(runs: list[tuple[pd.DataFrame, Replay]], out: Path, threshold: float, gate: float,
         marks: list[tuple[int, float, str]]) -> None:
    fig, axes = plt.subplots(len(runs), 1, figsize=(12, 3.3 * len(runs) + 0.5), squeeze=False)
    for k, (ax, (df, result)) in enumerate(zip(axes[:, 0], runs), start=1):
        t = df["sim_t_h"]
        for name in loop_names(df):
            ok = judged(df, name, gate)
            y = article_scale(df, name)
            line = ax.plot(t, y, lw=1.0, alpha=0.6, label=name)[0]
            ax.scatter(t[ok], y[ok], s=14, color=line.get_color())
            ax.scatter(t[~ok], y[~ok], s=14, facecolors="none", edgecolors=line.get_color())
        ax.axhline(threshold, color="#ef5350", ls="--", lw=1.2, label=f"limite {threshold:g}")
        for i, (a, b) in enumerate(false_spans(t, result.healthy)):
            ax.axvspan(a, b, color="#ef5350", alpha=0.12, lw=0,
                       label="ControlLoopsHealthy False (refeito)" if i == 0 else None)
        for index, tm, label in marks:
            if index == k:
                ax.axvline(tm, color="#ff9800", lw=1.4)
                ax.annotate(label, (tm, 0.04), xycoords=("data", "axes fraction"), xytext=(3, 0),
                            textcoords="offset points", fontsize=9, color="#e65100")
        ax.set_ylim(0, 1)
        ax.set_ylabel("PI (escala do artigo)")
        ax.set_title(result.label, fontsize=10)
        ax.grid(alpha=0.3)
    # Uma legenda só, no topo, para não cobrir as marcas de cada painel.
    handles, labels = {}, {}
    for ax in axes[:, 0]:
        for h, lab in zip(*ax.get_legend_handles_labels()):
            handles.setdefault(lab, h)
    fig.legend(list(handles.values()), list(handles.keys()), loc="upper center", ncol=5, fontsize=9,
               frameon=False)
    axes[-1, 0].set_xlabel("tempo simulado — clock.t_h (h)")
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.45 / (3.3 * len(runs) + 0.5)))
    fig.savefig(out, dpi=130)
    print(f"[loop-rereading] figura → {out}")


def fmt(t: float | None) -> str:
    return "—" if t is None else f"{t:.2f}"


def main() -> None:
    ap = argparse.ArgumentParser(description="Releitura do Predictability Index na escala do artigo")
    ap.add_argument("--nominal", type=Path, required=True, help="gravação nominal usada para calibrar o limite")
    ap.add_argument("--run", type=Path, action="append", required=True, help="gravação a refazer (pode repetir)")
    ap.add_argument("--label", action="append", default=[], help="rótulo de cada --run, na mesma ordem")
    ap.add_argument("--threshold", type=float, help="limite na escala do artigo (default: calibrado na nominal)")
    ap.add_argument("--margin", type=float, default=0.05, help="folga abaixo do mínimo nominal (default 0,05)")
    ap.add_argument("--gate", type=float, default=0.05, help="minOutputStd da política, em %% (default 0,05)")
    ap.add_argument("--persistence", type=int, default=3, help="avaliações ruins seguidas (default 3)")
    ap.add_argument("--plot", type=int, action="append", default=[],
                    help="índice (1, 2, ...) de um --run a desenhar (pode repetir; default: todos)")
    ap.add_argument("--mark", action="append", default=[], metavar="I:T:ROTULO",
                    help="marco vertical no painel do --run I, em clock.t_h (pode repetir)")
    ap.add_argument("--out", type=Path, help="PNG de saída (sem --out, só a tabela)")
    args = ap.parse_args()

    threshold, low, high = calibrate(load(args.nominal), args.margin)
    if args.threshold is not None:
        threshold = args.threshold
    print(f"[loop-rereading] nominal ({args.nominal.name}): PI_artigo de {low:.3f} a {high:.3f}; "
          f"limite {threshold:g}, portão {args.gate:g} %, persistência {args.persistence}")

    labels = args.label + [path.stem for path in args.run[len(args.label):]]
    runs = []
    for path, label in zip(args.run, labels):
        df = load(path)
        result = replay(df, label, threshold, args.gate, args.persistence)
        runs.append((df, result))
        firsts = ", ".join(f"{name} {fmt(t)}" for name, t in result.first_bad.items())
        print(f"  {label}: {result.evaluations} avaliações; LOOPS False em {fmt(result.first_false)} "
              f"({', '.join(result.flagged_at_first_false) or 'nenhuma malha'}), "
              f"{100 * result.false_fraction:.0f} % das avaliações False; primeira avaliação ruim: {firsts}")

    if args.out:
        chosen = [runs[i - 1] for i in args.plot] if args.plot else runs
        index_map = {i: k for k, i in enumerate(args.plot or range(1, len(runs) + 1), start=1)}
        marks = [(index_map[i], tm, label) for i, tm, label in map(parse_mark, args.mark) if i in index_map]
        plot(chosen, args.out, threshold, args.gate, marks)


if __name__ == "__main__":
    main()
