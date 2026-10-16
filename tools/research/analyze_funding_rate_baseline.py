"""Compute pre-trade baseline statistics for the offline funding-arbitrage study."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


RESEARCH_ROOT = Path("data/research/funding_rate_arbitrage")
INPUT = RESEARCH_ROOT / "funding_price_events.csv"
OUTPUT = RESEARCH_ROOT / "funding_stage2_baseline.json"
PERIODS_PER_DAY = 3
DAYS_PER_YEAR = 365
APR_FACTOR = PERIODS_PER_DAY * DAYS_PER_YEAR
BASE_FEE_ONE_LEG_PCT = 0.30
BASE_FEE_CAPITAL_PCT = 0.15


def percentiles(values: pd.Series, percentiles: list[float]) -> dict[str, float]:
    return {f"p{int(percentile * 100)}": float(values.quantile(percentile)) for percentile in percentiles}


def episode_summary(mask: pd.Series, timestamps: pd.Series) -> dict[str, float | int]:
    """Summarize contiguous true runs; one funding interval is eight hours."""
    groups = mask.ne(mask.shift()).cumsum()
    runs = []
    for _, group in pd.DataFrame({"active": mask, "time": timestamps, "group": groups}).groupby("group"):
        if not bool(group["active"].iloc[0]):
            continue
        # A run of n funding records spans n payment intervals, including its first interval.
        duration_hours = len(group) * 8
        runs.append(duration_hours)
    result: dict[str, float | int] = {"episode_count": len(runs)}
    if runs:
        series = pd.Series(runs, dtype="float64")
        result.update(
            {
                "median_duration_hours": float(series.median()),
                "p75_duration_hours": float(series.quantile(0.75)),
                "max_duration_hours": float(series.max()),
            }
        )
    return result


def period_summary(frame: pd.DataFrame) -> dict:
    apr_pct = frame["funding_rate"] * APR_FACTOR * 100
    rolling_apr_pct = frame["rolling_funding_rate_3"] * APR_FACTOR * 100
    positive = int((frame["funding_rate"] > 0).sum())
    negative = int((frame["funding_rate"] < 0).sum())
    zero = int((frame["funding_rate"] == 0).sum())
    thresholds = {}
    for threshold in (5.0, 10.0, 15.0):
        thresholds[str(int(threshold))] = episode_summary(rolling_apr_pct > threshold, frame["funding_time_ms"])
    return {
        "funding_record_count": int(len(frame)),
        "positive_rate_pct": positive / len(frame) * 100,
        "negative_rate_pct": negative / len(frame) * 100,
        "zero_rate_pct": zero / len(frame) * 100,
        "realized_apr_pct_percentiles": percentiles(apr_pct, [0.25, 0.5, 0.75, 0.9]),
        "rolling_3_realized_apr_pct_percentiles": percentiles(rolling_apr_pct.dropna(), [0.25, 0.5, 0.75, 0.9]),
        "gross_continuous_funding_apr_pct_of_futures_notional": float(frame["funding_rate"].mean() * APR_FACTOR * 100),
        "rolling_apr_threshold_episodes": thresholds,
    }


def main() -> None:
    data = pd.read_csv(INPUT)
    data["funding_time"] = pd.to_datetime(data["funding_time_ms"], unit="ms", utc=True)
    data = data.sort_values("funding_time_ms", kind="stable").reset_index(drop=True)
    data["rolling_funding_rate_3"] = data["funding_rate"].rolling(3, min_periods=3).mean()
    modern = data[data["funding_time"] >= pd.Timestamp("2023-01-01", tz="UTC")].copy()
    complete = data[data["complete_for_execution"]].copy()

    continuous_apr_capital_pct = data["funding_rate"].mean() * APR_FACTOR * 100 / 2
    modern_apr_capital_pct = modern["funding_rate"].mean() * APR_FACTOR * 100 / 2
    result = {
        "scope": "Baseline observation only. No entry/exit episode, fee realization, or return simulation is performed.",
        "funding_data": {
            "first_time_utc": data["funding_time"].iloc[0].isoformat(),
            "last_time_utc": data["funding_time"].iloc[-1].isoformat(),
            "interval_hours_declared_unique": sorted(data["funding_interval_hours"].unique().tolist()),
        },
        "all_available": period_summary(data),
        "since_2023": period_summary(modern),
        "basis_pct_on_complete_price_events": {
            "complete_event_count": int(len(complete)),
            "censored_event_count": int((~data["complete_for_execution"]).sum()),
            "mark_minus_spot_pct_percentiles": percentiles(complete["mark_basis_pct"], [0.1, 0.25, 0.5, 0.75, 0.9]),
            "futures_execution_minus_spot_pct_percentiles": percentiles(complete["execution_basis_pct"], [0.1, 0.25, 0.5, 0.75, 0.9]),
        },
        "fee_checkpoint": {
            "base_round_trip_fee_pct_of_one_leg_notional": BASE_FEE_ONE_LEG_PCT,
            "base_round_trip_fee_pct_of_two_leg_capital_approx": BASE_FEE_CAPITAL_PCT,
            "gross_continuous_funding_apr_pct_of_two_leg_capital_all_available": float(continuous_apr_capital_pct),
            "gross_continuous_funding_apr_pct_of_two_leg_capital_since_2023": float(modern_apr_capital_pct),
            "break_even_hold_days_at_average_funding_all_available": float(BASE_FEE_CAPITAL_PCT / (continuous_apr_capital_pct / DAYS_PER_YEAR)),
            "break_even_hold_days_at_average_funding_since_2023": float(BASE_FEE_CAPITAL_PCT / (modern_apr_capital_pct / DAYS_PER_YEAR)),
            "interpretation_limit": "This is a continuous-hold arithmetic checkpoint only. It excludes basis movement, negative funding during a position, censored events, spread, slippage, and actual threshold-driven turnover.",
        },
    }
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
