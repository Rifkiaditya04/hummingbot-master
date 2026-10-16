from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("data/research/funding_rate_arbitrage/raw")
OUTPUT = ROOT.parent / "price_coverage_audit.json"
MONTHS = pd.date_range("2020-01-01", "2026-08-01", freq="MS")
SOURCES = ("spot", "futures", "mark")
ONE_MINUTE_MS = 60_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_source(source: str) -> dict:
    files = []
    total_rows = 0
    all_gaps: list[dict] = []
    first_timestamp = None
    previous_last_timestamp = None
    last_timestamp = None

    for month in MONTHS:
        label = month.strftime("%Y-%m")
        path = ROOT / source / f"BTCUSDT-1m-{label}.zip"
        if not path.exists():
            raise FileNotFoundError(f"Missing archive: {path}")

        raw_timestamps = pd.read_csv(path, header=None, usecols=[0]).iloc[:, 0]
        numeric_timestamps = pd.to_numeric(raw_timestamps, errors="coerce")
        skipped_non_numeric_rows = int(numeric_timestamps.isna().sum())
        source_timestamps = numeric_timestamps.dropna().astype("int64").to_numpy()
        timestamp_unit = "microseconds" if int(np.median(source_timestamps)) > 10**14 else "milliseconds"
        if timestamp_unit == "microseconds":
            if np.any(source_timestamps % 1_000 != 0):
                raise ValueError(f"Microsecond timestamp is not millisecond-aligned: {path}")
            timestamps = source_timestamps // 1_000
        else:
            timestamps = source_timestamps
        if len(timestamps) == 0:
            raise ValueError(f"Empty archive: {path}")

        deltas = np.diff(timestamps)
        bad_positions = np.flatnonzero(deltas != ONE_MINUTE_MS)
        month_gaps = [
            {
                "after_open_time_utc_ms": int(timestamps[index]),
                "next_open_time_utc_ms": int(timestamps[index + 1]),
                "delta_ms": int(deltas[index]),
            }
            for index in bad_positions[:10]
        ]
        if previous_last_timestamp is not None:
            cross_month_delta = int(timestamps[0] - previous_last_timestamp)
            if cross_month_delta != ONE_MINUTE_MS:
                month_gaps.append(
                    {
                        "after_open_time_utc_ms": int(previous_last_timestamp),
                        "next_open_time_utc_ms": int(timestamps[0]),
                        "delta_ms": cross_month_delta,
                    }
                )

        files.append(
            {
                "month": label,
                "file": str(path),
                "rows": int(len(timestamps)),
                "skipped_non_numeric_rows": skipped_non_numeric_rows,
                "source_timestamp_unit": timestamp_unit,
                "first_open_time_utc_ms": int(timestamps[0]),
                "last_open_time_utc_ms": int(timestamps[-1]),
                "sha256": sha256(path),
                "continuity_break_count": int(len(bad_positions) + (1 if previous_last_timestamp is not None and timestamps[0] - previous_last_timestamp != ONE_MINUTE_MS else 0)),
                "continuity_break_samples": month_gaps,
            }
        )
        all_gaps.extend({"month": label, **gap} for gap in month_gaps)
        total_rows += len(timestamps)
        first_timestamp = int(timestamps[0]) if first_timestamp is None else first_timestamp
        previous_last_timestamp = int(timestamps[-1])
        last_timestamp = int(timestamps[-1])

    return {
        "source": source,
        "archive_count": len(files),
        "total_rows": int(total_rows),
        "first_open_time_utc_ms": first_timestamp,
        "last_open_time_utc_ms": last_timestamp,
        "continuity_break_count": len(all_gaps),
        "continuity_break_samples": all_gaps[:20],
        "files": files,
    }


def main() -> None:
    audit = {
        "method": "Monthly official Binance 1m archives; first-column UTC millisecond continuity is checked within and across months.",
        "expected_months": [month.strftime("%Y-%m") for month in MONTHS],
        "sources": {source: audit_source(source) for source in SOURCES},
    }
    OUTPUT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    for source, result in audit["sources"].items():
        print(source, result["archive_count"], result["total_rows"], result["continuity_break_count"], flush=True)


if __name__ == "__main__":
    main()
