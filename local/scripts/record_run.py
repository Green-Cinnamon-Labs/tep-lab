"""
record_run.py — grava o veredito do supervisor ao longo do tempo, num CSV.

O `Plant.status` guarda só a avaliação mais recente. Para calibrar limiares (bloco 6 da spec #85) e
para o experimento #82, é preciso a série no tempo: este script lê o `Plant` pelo kubectl a cada
`--interval` segundos e grava uma linha com o tempo simulado da planta (`clock.t_h`, lido do
historian), o custo J, a fase, as conditions e, para cada malha de controle da política ativa, o
Predictability Index, o offset, o σ da válvula e se a malha foi julgada.

Só usa a biblioteca padrão do Python (chama `kubectl` e o historian por HTTP) — roda em qualquer
Python 3.9+, sem instalar nada. Para com Ctrl+C.

Uso:
    python tep-lab/local/scripts/record_run.py --out tep-lab/data/experiment_82/calibracao.csv
    python tep-lab/local/scripts/record_run.py --interval 10 --plant tep --out run.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CONDITIONS = [
    "DataAvailable",
    "CostWithinBudget",
    "TargetsMet",
    "ConstraintsSatisfied",
    "PolicyCompliant",
    "ControlLoopsHealthy",
]
LOOP_FIELDS = ["pi", "offset", "output_std", "evaluated", "healthy", "reason"]


def kubectl_json(*args: str) -> dict:
    out = subprocess.run(["kubectl", *args, "-o", "json"], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def sim_time_h(historian: str) -> float | None:
    """Último valor de `clock.t_h` no historian (tempo simulado, em horas)."""
    body = json.dumps({"keys": ["clock.t_h"], "window_s": 5}).encode()
    req = urllib.request.Request(f"{historian}/aggregate", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            stats = json.load(resp)["signals"].get("clock.t_h")
            return stats["last"] if stats else None
    except Exception:  # noqa: BLE001 — historian fora do ar vira célula vazia, não interrompe a gravação
        return None


def loop_names(plant: dict, namespace: str) -> list[str]:
    """Nomes das malhas declaradas na política ativa (definem as colunas do CSV)."""
    policy = kubectl_json("get", "operatingpolicy", plant["spec"]["policyRef"], "-n", namespace)
    return [loop["name"] for loop in policy["spec"].get("controlLoops", [])]


def row(plant: dict, loops: list[str], historian: str) -> dict:
    status = plant.get("status", {})
    conditions = {c["type"]: c["status"] for c in status.get("conditions", [])}
    cost = status.get("cost") or {}
    by_loop = {loop["name"]: loop for loop in status.get("loops", [])}

    r = {
        "wall_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sim_t_h": sim_time_h(historian),
        "last_evaluation_time": status.get("lastEvaluationTime"),
        "phase": status.get("phase"),
        "active_policy": status.get("activePolicy"),
        "cost": cost.get("value"),
        "cost_unit": cost.get("unit"),
        "max_cost": cost.get("maxCost"),
        "consecutive_violations": status.get("consecutiveViolations", 0),
        "consecutive_loop_violations": status.get("consecutiveLoopViolations", 0),
    }
    for c in CONDITIONS:
        r[c] = conditions.get(c)
    for name in loops:
        loop = by_loop.get(name, {})
        r[f"{name}.pi"] = loop.get("predictability")
        r[f"{name}.offset"] = loop.get("offset")
        r[f"{name}.output_std"] = loop.get("outputStd")
        r[f"{name}.evaluated"] = loop.get("evaluated")
        r[f"{name}.healthy"] = loop.get("healthy")
        r[f"{name}.reason"] = loop.get("reason")
    return r


def main() -> int:
    # Console do Windows usa cp1252 por padrão: força UTF-8 para acentos e setas.
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Grava o veredito do Plant ao longo do tempo num CSV.")
    ap.add_argument("--out", required=True, help="Arquivo CSV de saída (pastas são criadas)")
    ap.add_argument("--plant", default="tep", help="Nome do Plant (default: tep)")
    ap.add_argument("--namespace", default="default")
    ap.add_argument("--historian", default="http://localhost:8090", help="URL do historian, para clock.t_h")
    ap.add_argument("--interval", type=float, default=10.0, help="Segundos entre leituras (default: 10)")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    plant = kubectl_json("get", "plant", args.plant, "-n", args.namespace)
    loops = loop_names(plant, args.namespace)
    header = list(row(plant, loops, args.historian).keys())

    print(f"[record] gravando {args.plant} a cada {args.interval:g} s em {out} — malhas: {', '.join(loops) or 'nenhuma'}")
    print("[record] Ctrl+C para parar")
    written = 0
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        try:
            while True:
                try:
                    plant = kubectl_json("get", "plant", args.plant, "-n", args.namespace)
                    r = row(plant, loops, args.historian)
                    writer.writerow(r)
                    f.flush()
                    written += 1
                    pis = "  ".join(f"{n}={r[f'{n}.pi']:.2f}" if r[f"{n}.pi"] is not None else f"{n}=--" for n in loops)
                    print(f"[record] {r['wall_time']}  t={r['sim_t_h']}  J={r['cost']}  {r['phase']}  loops={r['ControlLoopsHealthy']}  {pis}")
                except subprocess.CalledProcessError as e:
                    print(f"[record] kubectl falhou: {e.stderr.strip()}", file=sys.stderr)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            pass
    print(f"\n[record] {written} linhas gravadas em {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
