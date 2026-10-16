from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("data/research/funding_rate_arbitrage/raw/funding_rate")
OUT = Path("data/research/funding_rate_arbitrage/funding_stage2_partial.json")
THRESHOLDS = (0.05, 0.10, 0.15)


def episodes_above(values: pd.Series, threshold: float) -> list[int]:
    mask = values > threshold
    starts = mask & ~mask.shift(1, fill_value=False)
    lengths = []
    for start in mask.index[starts]:
        after = mask.loc[start:]
        first_false = after[~after]
        end = first_false.index[0] if not first_false.empty else after.index[-1] + 1
        lengths.append(int(mask.loc[start:end].sum()))
    return lengths


def summary(data: pd.DataFrame) -> dict:
    apr = data["apr"]
    output = {
        "records": int(len(data)),
        "positive_rate_pct": float((data["funding_rate"] > 0).mean() * 100),
        "negative_rate_pct": float((data["funding_rate"] < 0).mean() * 100),
        "zero_rate_pct": float((data["funding_rate"] == 0).mean() * 100),
        "apr_percentiles_pct": {str(q): float(apr.quantile(q) * 100) for q in (0.25, 0.5, 0.75, 0.9)},
        "gross_realized_funding_apr_pct": float(data["funding_rate"].mean() * 3 * 365 * 100),
        "threshold_episodes": {},
    }
    for threshold in THRESHOLDS:
        lengths = episodes_above(apr, threshold)
        output["threshold_episodes"][f"{threshold * 100:.0f}%"] = {
            "episodes": len(lengths),
            "median_funding_intervals": float(np.median(lengths)) if lengths else None,
            "median_hours": float(np.median(lengths) * 8) if lengths else None,
            "p75_hours": float(np.quantile(lengths, 0.75) * 8) if lengths else None,
            "max_hours": int(max(lengths) * 8) if lengths else None,
        }
    return output


def main() -> None:
    frames = []
    for path in sorted(ROOT.glob("BTCUSDT-fundingRate-*.zip")):
        with zipfile.ZipFile(path) as archive:
            frame = pd.read_csv(archive.open(archive.namelist()[0]))
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)
    data["timestamp"] = pd.to_datetime(data["calc_time"], unit="ms", utc=True)
    data["funding_rate"] = pd.to_numeric(data["last_funding_rate"])
    data["apr"] = data["funding_rate"] * 3 * 365
    data = data.sort_values("timestamp").reset_index(drop=True)
    report = {
        "all_available": summary(data),
        "since_2023": summary(data[data["timestamp"] >= pd.Timestamp("2023-01-01", tz="UTC")]),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
