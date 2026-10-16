from unittest import TestCase

from hummingbot.data_feed.candles_feed.binance_spot_candles import BinanceDemoSpotCandles
from hummingbot.data_feed.candles_feed.candles_factory import CandlesFactory
from hummingbot.data_feed.candles_feed.data_types import CandlesConfig


class TestBinanceDemoCandles(TestCase):
    def test_factory_creates_demo_candle_feed_with_demo_endpoints(self):
        candle = CandlesFactory.get_candle(CandlesConfig(
            connector="binance_demo",
            trading_pair="BTC-USDT",
            interval="5m",
            max_records=200,
        ))

        self.assertIsInstance(candle, BinanceDemoSpotCandles)
        self.assertEqual("https://demo-api.binance.com", candle.rest_url)
        self.assertEqual("wss://demo-stream.binance.com:9443/ws", candle.wss_url)

