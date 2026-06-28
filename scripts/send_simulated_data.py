#!/usr/bin/env python3
"""Envoie les lignes de data/simulated_sensor.txt vers ThingsBoard, une par une."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installer les dependances : pip install -r requirements.txt")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "simulated_sensor.txt"
SECRETS_H = ROOT / "secrets.h"
INDEX_FILE = ROOT / "data" / ".last_index"

READING_RE = re.compile(r"^#(\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)\s*$")
_TOKEN_RE = re.compile(r'#define\s+TB_ACCESS_TOKEN\s+"([^"]+)"', re.I)
_HOST_RE = re.compile(r'#define\s+TB_HOST\s+"([^"]+)"', re.I)
_LAT_RE = re.compile(r'#define\s+DEVICE_LATITUDE\s+([-\d.]+)', re.I)
_LON_RE = re.compile(r'#define\s+DEVICE_LONGITUDE\s+([-\d.]+)', re.I)


def _read_secrets_h() -> str:
    return SECRETS_H.read_text(encoding="utf-8") if SECRETS_H.is_file() else ""


def load_host_from_secrets() -> str:
    env = os.environ.get("TB_HOST", "").strip()
    if env:
        return env
    match = _HOST_RE.search(_read_secrets_h())
    return match.group(1).strip() if match else "eu.thingsboard.cloud"


def load_position() -> tuple[float, float]:
    text = _read_secrets_h()
    lat_m = _LAT_RE.search(text)
    lon_m = _LON_RE.search(text)
    lat = float(lat_m.group(1)) if lat_m else 14.6928
    lon = float(lon_m.group(1)) if lon_m else -17.4467
    return lat, lon


def tb_http_base() -> str:
    explicit = os.environ.get("TB_HTTP_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    return f"https://{load_host_from_secrets()}/api/v1"


def load_token_from_secrets() -> str:
    match = _TOKEN_RE.search(_read_secrets_h())
    if not match:
        return ""
    token = match.group(1).strip()
    if not token or "VOTRE" in token or "REMPLACER" in token:
        return ""
    return token


def resolve_token(cli_token: str) -> str:
    return cli_token or os.environ.get("TB_ACCESS_TOKEN", "").strip() or load_token_from_secrets()


def load_readings(path: Path) -> list[tuple[float, float]]:
    readings: list[tuple[float, float]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        match = READING_RE.match(line)
        if match:
            readings.append((float(match.group(1)), float(match.group(2))))
    if not readings:
        raise ValueError(f"Aucune ligne #humidite, temperature dans {path}")
    return readings


def load_index() -> int:
    if INDEX_FILE.is_file():
        try:
            return int(INDEX_FILE.read_text(encoding="utf-8").strip())
        except ValueError:
            pass
    return 0


def save_index(index: int) -> None:
    INDEX_FILE.write_text(str(index), encoding="utf-8")


def to_payload(humidity: float, temperature: float) -> dict:
    lat, lon = load_position()
    return {
        "humidity": humidity,
        "temperature": temperature,
        "latitude": lat,
        "longitude": lon,
    }


def format_line(humidity: float, temperature: float) -> str:
    return f"#{humidity:.0f}, {temperature:.1f}"


def send_once(token: str, payload: dict) -> None:
    url = f"{tb_http_base()}/{token}/telemetry"
    response = requests.post(url, json=payload, timeout=15)
    if response.status_code == 401:
        print(f"Erreur 401 — verifiez token et region ({load_host_from_secrets()}).")
        sys.exit(1)
    response.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--interval", type=float, default=10.0)
    parser.add_argument("--token", default="")
    parser.add_argument("--reset", action="store_true", help="Repartir de la 1re ligne")
    args = parser.parse_args()

    token = resolve_token(args.token)
    if not token:
        print("Token manquant (secrets.h, --token ou TB_ACCESS_TOKEN).")
        sys.exit(1)
    if not args.file.exists():
        print(f"Fichier introuvable : {args.file}")
        sys.exit(1)

    readings = load_readings(args.file)
    index = 0 if args.reset else load_index()
    total = len(readings)

    def send_next() -> bool:
        nonlocal index
        if index >= total:
            return False
        humidity, temperature = readings[index]
        payload = to_payload(humidity, temperature)
        send_once(token, payload)
        print(f"[{index + 1}/{total}] {format_line(humidity, temperature)}  ->  TB OK")
        index += 1
        save_index(index)
        return True

    if args.interval <= 0:
        if not send_next():
            print("Fin du fichier — relancez avec --reset")
        return

    print(f"{total} lignes dans {args.file.name} — une envoi / {args.interval}s")
    try:
        while True:
            if not send_next():
                print("Fin du fichier — arret (ou --reset pour recommencer)")
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\nArret — prochaine ligne : {index + 1}/{total}")


if __name__ == "__main__":
    main()
