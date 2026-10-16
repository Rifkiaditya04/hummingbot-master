"""Build an auditable BTCUSDT funding-event dataset from official Binance archives.

This is an offline research utility. It never imports Hummingbot trading code,
connects to an exchange, or submits orders.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


RESEARCH_ROOT = Path("data/research/funding_rate_arbitrage")
RAW_ROOT = RESEARCH_ROOT / "raw"
FUNDING_DIR = RAW_ROOT / "funding_rate"
OUTPUT_CSV = RESEARCH_ROOT / "funding_price_events.csv"
AUDIT_JSON = RESEARCH_ROOT / "funding_price_join_audit.json"
ONE_MINUTE_MS = 60_000


def normalize_timestamp_ms(values: pd.Series, path: Path) -> tuple[pd.Series, str]:
    """Normalize Binance archive timestamps while preserving the declared source unit."""
    numeric = pd.to_numeric(values, errors="coerce")
    numeric = numeric.dropna().astype("int64")
    if numeric.empty:
        raise ValueError(f"No numeric timestamps in {path}")
    if int(numeric.median()) > 10**14:
        if (numeric % 1_000 != 0).any():
            raise ValueError(f"Microsecond timestamps are not millisecond-aligned in {path}")
        return numeric // 1_000, "microseconds"
    return numeric, "milliseconds"


def load_funding() -> pd.DataFrame:
    frames = []
    for path in sorted(FUNDING_DIR.glob("BTCUSDT-fundingRate-*.zip")):
        frame = pd.read_csv(path)
        required = {"calc_time", "funding_interval_hours", "last_funding_rate"}
        if not required.issubset(frame.columns):
            raise ValueError(f"Unexpected funding schema in {path}: {list(frame.columns)}")
        timestamps, unit = normalize_timestamp_ms(frame["calc_time"], path)
        frame = frame.loc[timestamps.index].copy()
        frame["funding_time_ms"] = timestamps.to_numpy()
        frame["funding_rate"] = pd.to_numeric(frame["last_funding_rate"], errors="raise")
        frame["funding_interval_hours"] = pd.to_numeric(frame["funding_interval_hours"], errors="raise")
        frame["funding_source_timestamp_unit"] = unit
        frame["funding_source_file"] = path.name
        frames.append(frame[["funding_time_ms", "funding_rate", "funding_interval_hours", "funding_source_timestamp_unit", "funding_source_file"]])

    funding = pd.concat(frames, ignore_index=True).sort_values("funding_time_ms", kind="stable")
    if funding["funding_time_ms"].duplicated().any():
        raise ValueError("Duplicate funding timestamps detected")
    if not (funding["funding_interval_hours"] == 8).all():
        raise ValueError("Funding interval is not consistently eight hours")
    return funding.reset_index(drop=True)


def load_required_prices(source: str, required_times_ms: set[int]) -> tuple[dict[int, float], dict[str, int]]:
    """Return only the 1m open prices needed for the funding event table."""
    results: dict[int, float] = {}
    unit_counts: dict[str, int] = {}
    for path in sorted((RAW_ROOT / source).glob("BTCUSDT-1m-*.zip")):
        raw = pd.read_csv(path, header=None, usecols=[0, 1])
        timestamps, unit = normalize_timestamp_ms(raw.iloc[:, 0], path)
        price = pd.to_numeric(raw.iloc[:, 1], errors="coerce")
        frame = pd.DataFrame({"timestamp_ms": timestamps, "open": price.loc[timestamps.index]})
        frame = frame.dropna(subset=["open"])
        selected = frame[frame["timestamp_ms"].isin(required_times_ms)]
        if selected["timestamp_ms"].duplicated().any():
            raise ValueError(f"Duplicate price timestamps in {path}")
        for timestamp, open_price in selected.itertuples(index=False):
            timestamp = int(timestamp)
            if timestamp in results:
                raise ValueError(f"Duplicate {source} price at {timestamp}")
            results[timestamp] = float(open_price)
        unit_counts[unit] = unit_counts.get(unit, 0) + 1
    return results, unit_counts


def main() -> None:
    funding = load_funding()
    funding["funding_minute_ms"] = funding["funding_time_ms"] // ONE_MINUTE_MS * ONE_MINUTE_MS
    funding["execution_minute_ms"] = funding["funding_minute_ms"] + ONE_MINUTE_MS
    required_at_funding = set(funding["funding_minute_ms"].astype(int))
    required_execution = set(funding["execution_minute_ms"].astype(int))

    spot_prices, spot_units = load_required_prices("spot", required_at_funding | required_execution)
    futures_prices, futures_units = load_required_prices("futures", required_execution)
    mark_prices, mark_units = load_required_prices("mark", required_at_funding)

    funding["spot_open_at_funding"] = funding["funding_minute_ms"].map(spot_prices)
    funding["mark_open_at_funding"] = funding["funding_minute_ms"].map(mark_prices)
    funding["spot_open_after_funding"] = funding["execution_minute_ms"].map(spot_prices)
    funding["futures_open_after_funding"] = funding["execution_minute_ms"].map(futures_prices)
    required_columns = [
        "spot_open_at_funding",
        "mark_open_at_funding",
        "spot_open_after_funding",
        "futures_open_after_funding",
    ]
    funding["complete_for_execution"] = funding[required_columns].notna().all(axis=1)
    funding["mark_basis_pct"] = (
        (funding["mark_open_at_funding"] - funding["spot_open_at_funding"])
        / funding["spot_open_at_funding"]
        * 100
    )
    funding["execution_basis_pct"] = (
        (funding["futures_open_after_funding"] - funding["spot_open_after_funding"])
        / funding["spot_open_after_funding"]
        * 100
    )
    funding["funding_time_utc"] = pd.to_datetime(funding["funding_time_ms"], unit="ms", utc=True).astype(str)
    funding["funding_minute_utc"] = pd.to_datetime(funding["funding_minute_ms"], unit="ms", utc=True).astype(str)
    funding["execution_minute_utc"] = pd.to_datetime(funding["execution_minute_ms"], unit="ms", utc=True).astype(str)

    audit = {
        "purpose": "Offline event-price pairing only; no strategy entry or exit simulation is performed.",
        "funding_records": int(len(funding)),
        "first_funding_time_utc": funding["funding_time_utc"].iloc[0],
        "last_funding_time_utc": funding["funding_time_utc"].iloc[-1],
        "complete_for_execution": int(funding["complete_for_execution"].sum()),
        "censored_for_missing_price_data": int((~funding["complete_for_execution"]).sum()),
        "censored_event_samples": funding.loc[
            ~funding["complete_for_execution"],
            ["funding_time_utc", *required_columns],
        ].head(20).to_dict(orient="records"),
        "price_timestamp_units_by_archive_count": {
            "spot": spot_units,
            "futures": futures_units,
            "mark": mark_units,
        },
        "price_rules": {
            "funding_mark_proxy": "mark 1m open on the minute containing fundingTime",
            "spot_mark_basis": "spot 1m open on the minute containing fundingTime",
            "execution_prices": "spot and futures 1m open on the first minute beginning after fundingTime",
        },
    }
    funding.to_csv(OUTPUT_CSV, index=False)
    AUDIT_JSON.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
