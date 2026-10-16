from decimal import Decimal
from typing import List, Optional

import pandas as pd
import talib
from pydantic import Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from hummingbot.core.data_type.common import PriceType, TradeType
from hummingbot.data_feed.candles_feed.data_types import CandlesConfig
from hummingbot.strategy_v2.controllers.directional_trading_controller_base import (
    DirectionalTradingControllerBase,
    DirectionalTradingControllerConfigBase,
)
from hummingbot.strategy_v2.executors.data_types import ConnectorPair
from hummingbot.strategy_v2.models.executor_actions import CreateExecutorAction, ExecutorAction


class HighConfidenceMomentumConfig(DirectionalTradingControllerConfigBase):
    controller_name: str = "high_confidence_momentum"
    market_connector_name: str = Field(
        default=None,
        json_schema_extra={
            "prompt": "Enter the public market-data connector, leave empty to derive it from the trading connector: ",
            "prompt_on_new": True,
        },
    )
    market_trading_pair: str = Field(
        default=None,
        json_schema_extra={
            "prompt": "Enter the public market-data trading pair, leave empty to reuse the trading pair: ",
            "prompt_on_new": True,
        },
    )
    candles_connector: str = Field(
        default=None,
        json_schema_extra={
            "prompt": "Enter the connector for candles data, leave empty to reuse the market-data connector: ",
            "prompt_on_new": True,
        },
    )
    candles_trading_pair: str = Field(
        default=None,
        json_schema_extra={
            "prompt": "Enter the trading pair for candles data, leave empty to reuse the market-data pair: ",
            "prompt_on_new": True,
        },
    )
    interval: str = Field(
        default="5m",
        json_schema_extra={
            "prompt": "Enter the candle interval (e.g. 1m, 5m, 15m, 1h): ",
            "prompt_on_new": True,
        },
    )
    trade_side_mode: str = Field(
        default="long_only",
        json_schema_extra={
            "prompt": "Enter trade side mode (long_only/short_only/both): ",
            "prompt_on_new": True,
        },
    )
    ema_fast_length: int = Field(default=50)
    ema_slow_length: int = Field(default=200)
    rsi_length: int = Field(default=14)
    adx_length: int = Field(default=14)
    atr_length: int = Field(default=14)
    bb_length: int = Field(default=20)
    bb_std: float = Field(default=2.0)
    min_confirmation_count: int = Field(default=5, ge=3, le=7)
    trend_buffer_pct: Decimal = Field(default=Decimal("0.0015"))
    rsi_long_threshold: float = Field(default=56.0)
    rsi_short_threshold: float = Field(default=44.0)
    rsi_overbought_limit: float = Field(default=68.0)
    rsi_oversold_limit: float = Field(default=32.0)
    adx_threshold: float = Field(default=16.0)
    min_atr_pct: Decimal = Field(default=Decimal("0.0018"))
    max_atr_pct: Decimal = Field(default=Decimal("0.03"))
    min_volume_ratio: float = Field(default=0.7)
    bb_long_min: float = Field(default=0.45)
    bb_long_max: float = Field(default=0.80)
    bb_short_min: float = Field(default=0.20)
    bb_short_max: float = Field(default=0.55)

    @field_validator("market_connector_name", mode="before")
    @classmethod
    def set_market_connector_name(cls, v, validation_info: ValidationInfo):
        if v is None or v == "":
            connector_name = validation_info.data.get("connector_name")
            if connector_name:
                return connector_name.replace("_paper_trade", "")
        return v

    @field_validator("market_trading_pair", mode="before")
    @classmethod
    def set_market_trading_pair(cls, v, validation_info: ValidationInfo):
        if v is None or v == "":
            return validation_info.data.get("trading_pair")
        return v

    @field_validator("candles_connector", mode="before")
    @classmethod
    def set_candles_connector(cls, v, validation_info: ValidationInfo):
        if v is None or v == "":
            return validation_info.data.get("market_connector_name") or validation_info.data.get("connector_name")
        return v

    @field_validator("candles_trading_pair", mode="before")
    @classmethod
    def set_candles_trading_pair(cls, v, validation_info: ValidationInfo):
        if v is None or v == "":
            return validation_info.data.get("market_trading_pair") or validation_info.data.get("trading_pair")
        return v

    @field_validator("trade_side_mode", mode="before")
    @classmethod
    def validate_trade_side_mode(cls, v: str) -> str:
        value = (v or "long_only").lower()
        if value not in {"long_only", "short_only", "both"}:
            raise ValueError("trade_side_mode must be one of: long_only, short_only, both")
        return value


class HighConfidenceMomentum(DirectionalTradingControllerBase):
    def __init__(self, config: HighConfidenceMomentumConfig, *args, **kwargs):
        self.config = config
        self.max_records = max(
            self.config.ema_slow_length + 20,
            self.config.bb_length + 20,
            self.config.atr_length + 20,
            self.config.adx_length + 20,
        )
        self._last_signal = None
        self._last_signal_log_ts = 0.0
        self._last_data_state = None
        self._last_price_fallback_log_ts = 0.0
        super().__init__(config, *args, **kwargs)
        if self.config.market_connector_name != self.config.connector_name:
            self.market_data_provider.remove_rate_sources([
                ConnectorPair(
                    connector_name=self.config.connector_name,
                    trading_pair=self.config.trading_pair,
                )
            ])
            self.market_data_provider.initialize_rate_sources([
                ConnectorPair(
                    connector_name=self.config.market_connector_name,
                    trading_pair=self.config.market_trading_pair,
                )
            ])

    @staticmethod
    def _format_gate_breakdown(prefix: str, gate_map: dict) -> str:
        ordered = [
            ("trend", gate_map[f"{prefix}_trend"]),
            ("adx", gate_map["adx"]),
            ("vol", gate_map["volatility"]),
            ("volume", gate_map["volume"]),
            ("momentum", gate_map[f"{prefix}_momentum"]),
            ("bb", gate_map[f"{prefix}_band"]),
            ("reclaim", gate_map[f"{prefix}_reclaim"]),
        ]
        return " ".join(f"{name}={int(bool(flag))}" for name, flag in ordered)

    def _get_reference_price(self) -> Optional[Decimal]:
        fallback_close = self.processed_data.get("status", {}).get("close")
        try:
            price = self.market_data_provider.get_price_by_type(
                self.config.market_connector_name,
                self.config.market_trading_pair,
                PriceType.MidPrice,
            )
            if price is not None and price > 0:
                return price
        except Exception as exc:
            now = self.market_data_provider.time()
            if now - self._last_price_fallback_log_ts >= 300:
                self.logger().warning(
                    f"[HCM] Falling back to candle close for reference price because "
                    f"{self.config.market_connector_name} {self.config.market_trading_pair} is not ready: {exc}"
                )
                self._last_price_fallback_log_ts = now

        if fallback_close is not None:
            try:
                fallback_price = Decimal(str(fallback_close))
                if fallback_price > 0:
                    return fallback_price
            except Exception:
                pass
        return None

    def get_candles_config(self) -> List[CandlesConfig]:
        return [CandlesConfig(
            connector=self.config.candles_connector,
            trading_pair=self.config.candles_trading_pair,
            interval=self.config.interval,
            max_records=self.max_records,
        )]

    def create_actions_proposal(self) -> List[ExecutorAction]:
        create_actions = []
        signal = self.processed_data["signal"]
        if signal != 0 and self.can_create_executor(signal):
            price = self._get_reference_price()
            if price is None:
                self.logger().warning(
                    f"[HCM] Skipping executor creation because no usable reference price is available "
                    f"for {self.config.market_connector_name} {self.config.market_trading_pair}."
                )
                return create_actions
            amount = self.config.total_amount_quote / price / Decimal(self.config.max_executors_per_side)
            trade_type = TradeType.BUY if signal > 0 else TradeType.SELL
            self.logger().info(
                f"[HCM] EXEC {trade_type.name} {self.config.connector_name} {self.config.trading_pair} "
                f"price={price:.2f} amount={amount:.6f} signal={signal}"
            )
            create_actions.append(CreateExecutorAction(
                controller_id=self.config.id,
                executor_config=self.get_executor_config(trade_type, price, amount)))

        return create_actions
    async def update_processed_data(self):
        now = self.market_data_provider.time()
        df = self.market_data_provider.get_candles_df(
            connector_name=self.config.candles_connector,
            trading_pair=self.config.candles_trading_pair,
            interval=self.config.interval,
            max_records=self.max_records,
        ).copy()

        # Use the last fully formed candle for signal generation.
        if len(df) > 1:
            df = df.iloc[:-1].copy()

        if df.empty or len(df) < self.max_records // 2:
            self.processed_data["signal"] = 0
            self.processed_data["features"] = pd.DataFrame()
            self.processed_data["status"] = {
                "state": "warming_up",
                "rows": int(len(df)),
                "required_rows": int(self.max_records // 2),
            }
            if self._last_data_state != "warming_up":
                self.logger().info(
                    f"[HCM] Warming up candles for {self.config.candles_connector} "
                    f"{self.config.candles_trading_pair} {self.config.interval}: "
                    f"rows={len(df)}/{self.max_records // 2}"
                )
                self._last_data_state = "warming_up"
            return

        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        volume = df["volume"].astype(float)

        df["ema_fast"] = talib.EMA(close, timeperiod=self.config.ema_fast_length)
        df["ema_slow"] = talib.EMA(close, timeperiod=self.config.ema_slow_length)
        df["rsi"] = talib.RSI(close, timeperiod=self.config.rsi_length)
        df["adx"] = talib.ADX(high, low, close, timeperiod=self.config.adx_length)
        df["atr"] = talib.ATR(high, low, close, timeperiod=self.config.atr_length)
        df["atr_pct"] = df["atr"] / df["close"]
        df["volume_sma"] = volume.rolling(20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_sma"]

        upper_band, middle_band, lower_band = talib.BBANDS(
            close,
            timeperiod=self.config.bb_length,
            nbdevup=self.config.bb_std,
            nbdevdn=self.config.bb_std,
        )
        df["bb_upper"] = upper_band
        df["bb_middle"] = middle_band
        df["bb_lower"] = lower_band
        band_range = (df["bb_upper"] - df["bb_lower"]).replace(0, pd.NA)
        df["bb_percent"] = ((df["close"] - df["bb_lower"]) / band_range).fillna(0.5)

        df["prev_close"] = df["close"].shift(1)
        df["prev_ema_fast"] = df["ema_fast"].shift(1)

        trend_up = (df["ema_fast"] > df["ema_slow"]) & (
            df["close"] > df["ema_slow"] * (1 + float(self.config.trend_buffer_pct))
        )
        trend_down = (df["ema_fast"] < df["ema_slow"]) & (
            df["close"] < df["ema_slow"] * (1 - float(self.config.trend_buffer_pct))
        )

        volume_ok = df["volume_ratio"] >= self.config.min_volume_ratio
        volatility_ok = (df["atr_pct"] >= float(self.config.min_atr_pct)) & (
            df["atr_pct"] <= float(self.config.max_atr_pct)
        )
        adx_ok = df["adx"] >= self.config.adx_threshold

        long_momentum_ok = (df["rsi"] >= self.config.rsi_long_threshold) & (
            df["rsi"] <= self.config.rsi_overbought_limit
        )
        short_momentum_ok = (df["rsi"] <= self.config.rsi_short_threshold) & (
            df["rsi"] >= self.config.rsi_oversold_limit
        )

        long_band_ok = (df["bb_percent"] >= self.config.bb_long_min) & (
            df["bb_percent"] <= self.config.bb_long_max
        )
        short_band_ok = (df["bb_percent"] >= self.config.bb_short_min) & (
            df["bb_percent"] <= self.config.bb_short_max
        )

        long_reclaim = (df["prev_close"] <= df["prev_ema_fast"]) & (df["close"] > df["ema_fast"])
        short_reclaim = (df["prev_close"] >= df["prev_ema_fast"]) & (df["close"] < df["ema_fast"])

        df["long_score"] = (
            trend_up.astype(int)
            + adx_ok.astype(int)
            + volatility_ok.astype(int)
            + volume_ok.astype(int)
            + long_momentum_ok.astype(int)
            + long_band_ok.astype(int)
            + long_reclaim.astype(int)
        )
        df["short_score"] = (
            trend_down.astype(int)
            + adx_ok.astype(int)
            + volatility_ok.astype(int)
            + volume_ok.astype(int)
            + short_momentum_ok.astype(int)
            + short_band_ok.astype(int)
            + short_reclaim.astype(int)
        )

        long_signal = long_reclaim & (df["long_score"] >= self.config.min_confirmation_count)
        short_signal = short_reclaim & (df["short_score"] >= self.config.min_confirmation_count)

        df["signal"] = 0
        if self.config.trade_side_mode in {"long_only", "both"}:
            df.loc[long_signal, "signal"] = 1
        if self.config.trade_side_mode in {"short_only", "both"}:
            df.loc[short_signal, "signal"] = -1

        status_columns = [
            "close",
            "ema_fast",
            "ema_slow",
            "rsi",
            "adx",
            "atr_pct",
            "volume_ratio",
            "bb_percent",
            "long_score",
            "short_score",
            "signal",
        ]
        latest = df.iloc[-1]
        signal = int(latest["signal"])
        latest_gate_map = {
            "adx": bool(adx_ok.iloc[-1]),
            "volatility": bool(volatility_ok.iloc[-1]),
            "volume": bool(volume_ok.iloc[-1]),
            "long_trend": bool(trend_up.iloc[-1]),
            "short_trend": bool(trend_down.iloc[-1]),
            "long_momentum": bool(long_momentum_ok.iloc[-1]),
            "short_momentum": bool(short_momentum_ok.iloc[-1]),
            "long_band": bool(long_band_ok.iloc[-1]),
            "short_band": bool(short_band_ok.iloc[-1]),
            "long_reclaim": bool(long_reclaim.iloc[-1]),
            "short_reclaim": bool(short_reclaim.iloc[-1]),
        }
        self.processed_data["signal"] = signal
        self.processed_data["features"] = df[status_columns].tail(10)
        self.processed_data["status"] = {
            "state": "ready",
            "signal": signal,
            "close": float(latest["close"]),
            "ema_fast": float(latest["ema_fast"]),
            "ema_slow": float(latest["ema_slow"]),
            "rsi": float(latest["rsi"]),
            "adx": float(latest["adx"]),
            "atr_pct": float(latest["atr_pct"]),
            "volume_ratio": float(latest["volume_ratio"]),
            "bb_percent": float(latest["bb_percent"]),
            "long_score": int(latest["long_score"]),
            "short_score": int(latest["short_score"]),
            "gates": latest_gate_map,
        }

        should_log = (
            self._last_signal != signal
            or now - self._last_signal_log_ts >= 300
            or self._last_data_state != "ready"
        )
        if should_log:
            long_gate_breakdown = self._format_gate_breakdown("long", latest_gate_map)
            short_gate_breakdown = self._format_gate_breakdown("short", latest_gate_map)
            self.logger().info(
                f"[HCM] {self.config.candles_connector} {self.config.candles_trading_pair} {self.config.interval} | "
                f"signal={signal} long={int(latest['long_score'])} short={int(latest['short_score'])} "
                f"close={float(latest['close']):.2f} rsi={float(latest['rsi']):.2f} "
                f"adx={float(latest['adx']):.2f} atr_pct={float(latest['atr_pct']):.4f} "
                f"vol_ratio={float(latest['volume_ratio']):.2f} bb_pct={float(latest['bb_percent']):.2f} "
                f"long_gates=[{long_gate_breakdown}] short_gates=[{short_gate_breakdown}]"
            )
            self._last_signal = signal
            self._last_signal_log_ts = now
            self._last_data_state = "ready"

