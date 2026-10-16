from __future__ import annotations

import json
import zipfile

import numpy as np
import pandas as pd


ARCHIVE = "data/research/funding_rate_arbitrage/timezone_audit/BTCUSDT-1m-2023-01.zip"
LOCAL = "docs/Bitcoin_BTCUSDT.csv"
START = pd.Timestamp("2023-01-01 00:00:00")
END = pd.Timestamp("2023-02-01 00:00:00")
COLUMNS = ["open", "high", "low", "close", "volume"]


def main():
    with zipfile.ZipFile(ARCHIVE) as archive:
        filename = archive.namelist()[0]
        official = pd.read_csv(archive.open(filename), header=None, usecols=[0, 1, 2, 3, 4, 5])
    official.columns = ["timestamp", *COLUMNS]
    official["timestamp"] = pd.to_datetime(official["timestamp"], unit="ms", utc=True).dt.tz_localize(None)

    chunks = []
    for chunk in pd.read_csv(LOCAL, parse_dates=["timestamp"], chunksize=250_000):
        selected = chunk[(chunk["timestamp"] >= START) & (chunk["timestamp"] < END)]
        if not selected.empty:
            chunks.append(selected[["timestamp", *COLUMNS]])
    local = pd.concat(chunks, ignore_index=True)

    results = []
    for offset_hours in range(-12, 13):
        shifted = local.copy()
        shifted["timestamp"] = shifted["timestamp"] + pd.Timedelta(hours=offset_hours)
        merged = official.merge(shifted, on="timestamp", suffixes=("_official", "_local"))
        matched = np.ones(len(merged), dtype=bool)
        for column in COLUMNS:
            matched &= np.isclose(
                merged[f"{column}_official"].to_numpy(float),
                merged[f"{column}_local"].to_numpy(float),
                rtol=0,
                atol=1e-8,
            )
        results.append({
            "local_to_utc_offset_hours": offset_hours,
            "timestamp_overlap_rows": int(len(merged)),
            "full_ohlcv_match_rows": int(matched.sum()),
            "all_overlapping_rows_match": bool(matched.all()) if len(merged) else False,
        })

    report = {
        "official_rows": int(len(official)),
        "local_rows": int(len(local)),
        "official_first": official.timestamp.min().isoformat(),
        "official_last": official.timestamp.max().isoformat(),
        "offset_results": results,
    }
    zero_offset = official.merge(local, on="timestamp", suffixes=("_official", "_local"))
    report["zero_offset_examples"] = [
        {
            "timestamp": row.timestamp.isoformat(),
            "official": {column: float(getattr(row, f"{column}_official")) for column in COLUMNS},
            "local": {column: float(getattr(row, f"{column}_local")) for column in COLUMNS},
        }
        for row in zero_offset.head(3).itertuples(index=False)
    ]
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
