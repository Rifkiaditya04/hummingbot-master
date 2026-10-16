from __future__ import annotations

import hashlib
import json
import argparse
from pathlib import Path

import pandas as pd
import requests


MONTHS = pd.date_range("2020-01-01", "2026-08-01", freq="MS")
SOURCES = {
    "spot": "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/",
    "futures": "https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1m/",
    "mark": "https://data.binance.vision/data/futures/um/monthly/markPriceKlines/BTCUSDT/1m/",
}
ROOT = Path("data/research/funding_rate_arbitrage/raw")


def download_verified(session: requests.Session, source: str, month: str) -> dict:
    name = f"BTCUSDT-1m-{month}.zip"
    directory = ROOT / source
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / name
    checksum = session.get(SOURCES[source] + name + ".CHECKSUM", timeout=30)
    checksum.raise_for_status()
    expected = checksum.text.split()[0].lower()
    if destination.exists():
        content = destination.read_bytes()
    else:
        response = session.get(SOURCES[source] + name, timeout=120)
        response.raise_for_status()
        content = response.content
        temporary = destination.with_suffix(".part")
        temporary.write_bytes(content)
        temporary.replace(destination)
    actual = hashlib.sha256(content).hexdigest().lower()
    if actual != expected:
        raise RuntimeError(f"checksum mismatch: {source}/{name}")
    return {"source": source, "month": month, "file": str(destination), "bytes": len(content), "sha256": actual}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default="2026-08-01")
    parser.add_argument("--write-manifest", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    months = pd.date_range(args.start, args.end, freq="MS")
    entries = []
    with requests.Session() as session:
        for month in months:
            label = month.strftime("%Y-%m")
            for source in SOURCES:
                entry = download_verified(session, source, label)
                entries.append(entry)
                print(source, label, "verified", entry["bytes"], flush=True)
    if args.write_manifest:
        (ROOT / "price_manifest.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print("verified_files=", len(entries))


if __name__ == "__main__":
    main()
