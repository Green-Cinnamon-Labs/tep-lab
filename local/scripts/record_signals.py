"""
record_signals.py — grava sinais da planta lidos do historian: um CSV de médias por janela.

Complementa o `record_run.py`, que grava o veredito do supervisor. Aqui vão os sinais que o
`Plant.status` não traz (nível do reator, composições, posição das válvulas...). A cada `--interval`
segundos de relógio, pede ao historian a média de cada sinal na última janela de mesma duração.

Na partida, recupera o que o historian ainda guarda (`--backfill`, em segundos de relógio): pede
janelas aninhadas, todas terminando agora, e tira a média de cada fatia pela diferença das somas
(média × contagem). O tempo de cada linha é a média de `clock.t_h` na própria fatia.

Uso (de C:\\Projetos\\tep):
    python tep-lab/local/scripts/record_signals.py --wait --out tep-lab/data/experiment_89/sinais.csv

Com `--wait`, fica esperando o historian subir: dá para ligar o gravador antes da planta e pegar a
rodada desde o primeiro segundo.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLOCK = "clock.t_h"
DEFAULT_KEYS = [
    "valve.purge.position", "xmeas.stream9.flow_rate", "xmeas.reactor.pressure", "xmeas.reactor.level",
    "xmeas.reactor.temperature", "xmeas.separator.temperature", "xmeas.separator.pressure",
    "xmeas.stream9.component.a", "xmeas.stream9.component.b", "xmeas.stream9.component.c",
    "xmeas.stream9.component.d", "xmeas.stream9.component.e", "xmeas.stream6.component.b",
    "xmeas.stream6.flow_rate", "xmeas.stream8.flow_rate", "xmeas.compressor.work", "xmeas.stream11.flow_rate",
    "xmeas.separator.level", "xmeas.stripper.level", "valve.separator_underflow.position",
    "valve.stripper_product.position",
]


def aggregate(url: str, keys: list[str], window: float) -> dict:
    body = json.dumps({"keys": keys, "window_s": window}).encode()
    req = urllib.request.Request(f"{url}/aggregate", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)["signals"]


def backfill(url: str, keys: list[str], step: float, span: float) -> list[dict]:
    """Fatias de `step` s do que o historian ainda guarda, da mais antiga para a mais nova."""
    now = datetime.now(timezone.utc)
    rows, prev = [], {}
    for i in range(1, int(span // step) + 1):
        agg = aggregate(url, keys, step * i)
        row = {"wall_time": (now - timedelta(seconds=step * (i - 0.5))).isoformat(timespec="seconds")}
        for k in keys:
            cur, old = agg.get(k) or {}, prev.get(k) or {}
            count, mean = cur.get("count") or 0, cur.get("mean")
            n = count - (old.get("count") or 0)
            row[k] = None if mean is None or n <= 0 else (count * mean - (old.get("count") or 0) * (old.get("mean") or 0.0)) / n
        if row[CLOCK] is None:
            break  # a janela já passou do que o historian guarda
        rows.append(row)
        prev = agg
    return rows[::-1]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    ap = argparse.ArgumentParser(description="Grava sinais do historian (média por janela) num CSV")
    ap.add_argument("--out", required=True, type=Path, help="Arquivo CSV de saída (pastas são criadas)")
    ap.add_argument("--historian", default="http://127.0.0.1:8090")
    ap.add_argument("--interval", type=float, default=30.0, help="Segundos de relógio por linha (default: 30)")
    ap.add_argument("--backfill", type=float, default=0.0, help="Segundos de relógio a recuperar na partida")
    ap.add_argument("--until", type=float, default=None, help="Para quando clock.t_h passar deste valor")
    ap.add_argument("--wait", action="store_true", help="Espera o historian subir antes de começar")
    ap.add_argument("--keys", nargs="+", default=DEFAULT_KEYS)
    args = ap.parse_args()

    keys = [CLOCK] + [k for k in args.keys if k != CLOCK]
    while args.wait:
        try:
            if (aggregate(args.historian, [CLOCK], 5).get(CLOCK) or {}).get("mean") is not None:
                print("[record-signals] historian no ar — gravando")
                break
        except OSError:
            pass
        time.sleep(2)
    header = ["wall_time", "sim_t_h"] + keys[1:]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()

        def write(row: dict) -> None:
            writer.writerow({"wall_time": row["wall_time"], "sim_t_h": row[CLOCK], **{k: row[k] for k in keys[1:]}})
            f.flush()

        if args.backfill > 0:
            past = backfill(args.historian, keys, args.interval, args.backfill)
            for row in past:
                write(row)
            print(f"[record-signals] {len(past)} linhas recuperadas do historian")

        failures = 0
        while True:
            time.sleep(args.interval)
            try:
                agg = aggregate(args.historian, keys, args.interval)
                failures = 0
            except OSError as err:
                failures += 1
                print(f"[record-signals] historian não respondeu ({err}); tentativa {failures}")
                if failures >= 10:
                    print("[record-signals] historian fora do ar — encerrando")
                    return
                continue
            row = {"wall_time": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            row.update({k: (agg.get(k) or {}).get("mean") for k in keys})
            if row[CLOCK] is None:
                continue
            write(row)
            if args.until is not None and row[CLOCK] >= args.until:
                print(f"[record-signals] clock.t_h = {row[CLOCK]:.2f} — encerrando")
                return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
