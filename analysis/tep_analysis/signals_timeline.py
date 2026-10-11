"""
signals_timeline.py — linha do tempo dos sinais gravados pelo `local/scripts/record_signals.py`.

Um painel por sinal, empilhados, todos no tempo simulado da planta (`clock.t_h`). Complementa o
`run_timeline.py` (que mostra o veredito do supervisor): aqui aparece o que a planta fez.

Marcos (`--mark 31.0:"feixe descoberto"`) viram linhas verticais em todos os painéis. Referências
(`--line xmeas.reactor.level=50:"mínimo da política"`) viram linhas horizontais no painel do sinal.
Com mais de um CSV, as rodadas são sobrepostas nos mesmos eixos (um `--label` por CSV, na ordem).

Uso (de dentro de tep-lab/analysis):
    poetry run signals-timeline ../data/experiment_89/pi_nominal_longo_sinais_2026-10-10.csv \\
        --mark 31.0:"feixe descoberto" --line xmeas.reactor.level=50:"mínimo da política"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

LABELS = {
    "valve.purge.position": "válvula de purga (%)",
    "xmeas.stream9.flow_rate": "vazão de purga (kscmh)",
    "xmeas.reactor.pressure": "pressão do reator (kPa)",
    "xmeas.reactor.level": "nível do reator (%)",
    "xmeas.reactor.temperature": "temperatura do reator (°C)",
    "xmeas.stream9.component.b": "inerte B na purga (mol %)",
    "xmeas.stream11.flow_rate": "vazão de produto (m³/h)",
    "xmeas.separator.level": "nível do separador (%)",
    "xmeas.stripper.level": "nível do stripper (%)",
    "xmeas.separator.temperature": "temperatura do separador (°C)",
    "xmeas.compressor.work": "trabalho do compressor (kW)",
}
DEFAULT_KEYS = ["valve.purge.position", "xmeas.reactor.pressure", "xmeas.reactor.level",
                "xmeas.stream9.component.b", "xmeas.reactor.temperature"]


def parse_mark(text: str) -> tuple[float, str]:
    t, _, label = text.partition(":")
    return float(t), label or t


def parse_line(text: str) -> tuple[str, float, str]:
    key, _, rest = text.partition("=")
    value, _, label = rest.partition(":")
    return key, float(value), label or value


def plot(runs: list[tuple[str, pd.DataFrame]], out: Path, keys: list[str], marks: list[tuple[float, str]],
         lines: list[tuple[str, float, str]], title: str) -> None:
    colors = ["#1f77b4", "#2ca02c", "#9467bd", "#8c564b"]
    fig, axes = plt.subplots(len(keys), 1, figsize=(12, 2.5 * len(keys) + 1), sharex=True, squeeze=False)
    axes = axes[:, 0]
    for ax, key in zip(axes, keys):
        for (run_label, df), color in zip(runs, colors):
            show = len(runs) > 1 and ax is axes[0]  # a legenda das rodadas vai só no primeiro painel
            ax.plot(df["sim_t_h"], df[key], color=color, lw=1.5, label=run_label if show else None)
        for line_key, value, label in lines:
            if line_key == key:
                ax.axhline(value, color="#ef5350", ls="--", lw=1.2, label=label)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(loc="lower left", fontsize=8)
        ax.set_ylabel(LABELS.get(key, key), fontsize=9)
        ax.grid(alpha=0.3)
    axes[-1].set_xlabel("tempo simulado — clock.t_h (h)")

    for tm, label in marks:
        for ax in axes:
            ax.axvline(tm, color="#ff9800", lw=1.3)
        axes[0].annotate(label, (tm, 1.0), xycoords=("data", "axes fraction"), xytext=(-3, 4),
                         textcoords="offset points", fontsize=8, color="#e65100", ha="right", rotation=30)

    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print(f"[signals-timeline] {sum(len(df) for _, df in runs)} linhas → {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Linha do tempo dos sinais gravados pelo record_signals.py")
    ap.add_argument("csv", type=Path, nargs="+", help="Um CSV por rodada")
    ap.add_argument("--label", action="append", default=[], help="Rótulo de cada rodada, na ordem dos CSVs")
    ap.add_argument("--out", type=Path, help="PNG de saída (default: ao lado do primeiro CSV, mesmo nome)")
    ap.add_argument("--keys", nargs="+", default=DEFAULT_KEYS, help="Sinais, um painel cada")
    ap.add_argument("--mark", action="append", default=[], metavar="T:ROTULO", help="marco vertical em clock.t_h")
    ap.add_argument("--line", action="append", default=[], metavar="SINAL=VALOR:ROTULO",
                    help="referência horizontal no painel de um sinal")
    ap.add_argument("--tmin", type=float, default=None, help="mostra só a partir deste clock.t_h")
    ap.add_argument("--title", default=None)
    args = ap.parse_args()

    runs = []
    for i, path in enumerate(args.csv):
        df = pd.read_csv(path).dropna(subset=["sim_t_h"]).sort_values("sim_t_h")
        if args.tmin is not None:
            df = df[df["sim_t_h"] >= args.tmin]
        runs.append((args.label[i] if i < len(args.label) else path.stem, df))
    plot(runs, args.out or args.csv[0].with_suffix(".png"), args.keys, [parse_mark(m) for m in args.mark],
         [parse_line(x) for x in args.line], args.title or args.csv[0].stem)


if __name__ == "__main__":
    main()
