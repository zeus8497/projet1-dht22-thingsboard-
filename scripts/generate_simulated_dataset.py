#!/usr/bin/env python3
"""Genere data/simulated_sensor.txt pour le script Python (simulation locale PC)."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "simulated_sensor.txt"


def generate_lines(count: int, seed: int) -> list[str]:
    random.seed(seed)
    lines: list[str] = []
    for _ in range(count):
        humidity = int(random.uniform(68, 94))
        temperature = round(random.uniform(22.0, 31.5), 1)
        lines.append(f"#{humidity}, {temperature:.1f}")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--count", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    header = (
        "# Simulation locale PC — script send_simulated_data.py\n"
        "# Format : #humidite, temperature\n"
        "# Wokwi : mesures reelles du capteur DHT22 (pas ce fichier)\n\n"
    )
    lines = generate_lines(args.count, args.seed)
    DATA_FILE.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK — {len(lines)} lignes -> {DATA_FILE.name}")


if __name__ == "__main__":
    main()
