from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import requests


BASE = "https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/"
OUT = Path("data/research/funding_rate_arbitrage/raw/funding_rate")
MANIFEST = OUT / "manifest.json"
MONTHS = pd.date_range("2020-01-01", "2026-08-01", freq="MS")


def get(url: str, timeout: int = 90) -> requests.Response:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    entries = []
    for month in MONTHS:
        label = month.strftime("%Y-%m")
        name = f"BTCUSDT-fundingRate-{label}.zip"
        destination = OUT / name
        checksum_url = BASE + name + ".CHECKSUM"
        expected = get(checksum_url, 30).text.split()[0].lower()
        if destination.exists():
            data = destination.read_bytes()
        else:
            data = get(BASE + name).content
            destination.write_bytes(data)
        actual = hashlib.sha256(data).hexdigest().lower()
        if actual != expected:
            raise RuntimeError(f"checksum mismatch: {name}")
        entries.append({"month": label, "file": name, "bytes": len(data), "sha256": actual})
        print(label, "verified", len(data))
    MANIFEST.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print("verified_months=", len(entries))


if __name__ == "__main__":
    main()
