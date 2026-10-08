"""
summarize_run.py — resume um CSV gravado pelo record_run.py.

Mostra os fatos que servem de base para escolher os limiares (bloco 6 da spec #85): a distribuição
do custo J, quanto tempo cada condition ficou True, e, por malha, a distribuição do Predictability
Index e do σ da válvula. Não escolhe limiar nenhum — a decisão é de quem está calibrando.

O supervisor reavalia a cada 30 s; se a gravação amostrou mais rápido, a mesma avaliação aparece em
várias linhas. Por isso cada avaliação (`last_evaluation_time`) conta uma vez só.

Só usa a biblioteca padrão do Python.

Uso:
    python tep-lab/local/scripts/summarize_run.py tep-lab/data/experiment_82/calibracao.csv
"""

from __future__ import annotations

import csv
import statistics
import sys
from collections import Counter

CONDITIONS = ["DataAvailable", "CostWithinBudget", "TargetsMet", "ConstraintsSatisfied", "PolicyCompliant", "ControlLoopsHealthy"]


def num(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def pct(values: list[float], q: float) -> float:
    """Percentil q (0–100) por interpolação linear."""
    s = sorted(values)
    k = (len(s) - 1) * q / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def describe(values: list[float], digits: int = 3) -> str:
    if not values:
        return "sem dados"
    f = lambda x: f"{x:.{digits}f}"  # noqa: E731
    sd = statistics.pstdev(values) if len(values) > 1 else 0.0
    return (
        f"n={len(values)}  média={f(statistics.fmean(values))}  σ={f(sd)}  "
        f"mín={f(min(values))}  p5={f(pct(values, 5))}  p25={f(pct(values, 25))}  "
        f"mediana={f(pct(values, 50))}  p75={f(pct(values, 75))}  p95={f(pct(values, 95))}  máx={f(max(values))}"
    )


def main() -> int:
    # Console do Windows usa cp1252 por padrão: força UTF-8 para acentos e setas.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    with open(sys.argv[1], newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("CSV vazio")
        return 1

    # Uma linha por avaliação do supervisor
    seen, evals = set(), []
    for r in rows:
        key = r.get("last_evaluation_time") or r["wall_time"]
        if key not in seen:
            seen.add(key)
            evals.append(r)

    loops = sorted({c.split(".")[0] for c in rows[0] if c.endswith(".pi")})
    t = [x for x in (num(r["sim_t_h"]) for r in rows) if x is not None]

    print(f"Arquivo: {sys.argv[1]}")
    print(f"Linhas gravadas: {len(rows)}  |  avaliações distintas do supervisor: {len(evals)}")
    print(f"Relógio: {rows[0]['wall_time']} → {rows[-1]['wall_time']}")
    if t:
        print(f"Tempo simulado: {min(t):.3f} h → {max(t):.3f} h  ({(max(t) - min(t)) * 60:.1f} min simulados)")
    print(f"Política: {', '.join(sorted({r['active_policy'] for r in evals if r['active_policy']}))}")

    print("\n== Nível econômico")
    costs = [x for x in (num(r["cost"]) for r in evals) if x is not None]
    unit = next((r["cost_unit"] for r in evals if r["cost_unit"]), "")
    print(f"J ({unit}): {describe(costs, 2)}")
    max_costs = {r["max_cost"] for r in evals if r["max_cost"]}
    if max_costs:
        print(f"maxCost na política: {', '.join(sorted(max_costs))}")
    print(f"Fases: {dict(Counter(r['phase'] for r in evals))}")

    print("\n== Conditions (fração das avaliações em True)")
    for c in CONDITIONS:
        vals = [r[c] for r in evals if r.get(c)]
        if vals:
            counts = Counter(vals)
            print(f"  {c:22s} True={counts.get('True', 0) / len(vals):5.1%}  {dict(counts)}")

    print("\n== Malhas de controle")
    for name in loops:
        pis = [x for x in (num(r[f"{name}.pi"]) for r in evals) if x is not None]
        stds = [x for x in (num(r[f"{name}.output_std"]) for r in evals) if x is not None]
        offsets = [x for x in (num(r[f"{name}.offset"]) for r in evals) if x is not None]
        judged = [r for r in evals if r[f"{name}.evaluated"] == "True"]
        unhealthy = [r for r in judged if r[f"{name}.healthy"] == "False"]
        reasons = Counter(r[f"{name}.reason"] for r in evals if r[f"{name}.reason"])
        print(f"\n  {name}")
        print(f"    PI          {describe(pis)}")
        print(f"    σ válvula   {describe(stds, 4)}")
        print(f"    offset      {describe(offsets)}")
        print(f"    julgada em {len(judged)}/{len(evals)} avaliações; abaixo do limiar em {len(unhealthy)}")
        if reasons:
            print(f"    motivos: {dict(reasons)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
