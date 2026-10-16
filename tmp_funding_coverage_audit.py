from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path("data/research/funding_rate_arbitrage/raw/funding_rate")
OUT = Path("data/research/funding_rate_arbitrage/funding_coverage_audit.json")


def main() -> None:
    frames = []
    for path in sorted(ROOT.glob("BTCUSDT-fundingRate-*.zip")):
        with zipfile.ZipFile(path) as archive:
            name = archive.namelist()[0]
            frame = pd.read_csv(archive.open(name))
        frame["source_file"] = path.name
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)
    data["calc_time"] = pd.to_datetime(data["calc_time"], unit="ms", utc=True)
    data["last_funding_rate"] = pd.to_numeric(data["last_funding_rate"], errors="coerce")
    data["funding_interval_hours"] = pd.to_numeric(data["funding_interval_hours"], errors="coerce")
    data = data.sort_values("calc_time").reset_index(drop=True)
    deltas = data["calc_time"].diff().dt.total_seconds().div(3600)
    missing_expected = []
    for previous, current, delta in zip(data["calc_time"].shift(), data["calc_time"], deltas):
        if pd.notna(delta) and delta > 8.01:
            missing_expected.append({"after": previous.isoformat(), "before": current.isoformat(), "hours": float(delta)})
    report = {
        "records": int(len(data)),
        "first_calc_time_utc": data["calc_time"].min().isoformat(),
        "last_calc_time_utc": data["calc_time"].max().isoformat(),
        "duplicate_calc_time": int(data["calc_time"].duplicated().sum()),
        "null_funding_rate": int(data["last_funding_rate"].isna().sum()),
        "interval_hours_distribution": {str(k): int(v) for k, v in data["funding_interval_hours"].value_counts(dropna=False).sort_index().items()},
        "actual_time_delta_hours_distribution": {str(k): int(v) for k, v in deltas.value_counts(dropna=False).sort_index().items()},
        "gaps_over_8_hours": missing_expected,
        "first_rows": data.head(3).assign(calc_time=lambda x: x.calc_time.astype(str)).to_dict("records"),
        "last_rows": data.tail(3).assign(calc_time=lambda x: x.calc_time.astype(str)).to_dict("records"),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
