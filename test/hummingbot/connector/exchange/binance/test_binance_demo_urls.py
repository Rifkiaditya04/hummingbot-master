from unittest import TestCase

from hummingbot.connector.exchange.binance import binance_web_utils


class TestBinanceDemoUrls(TestCase):
    def test_demo_rest_endpoints(self):
        self.assertEqual(
            "https://demo-api.binance.com/api/v3/ping",
            binance_web_utils.public_rest_url("/ping", domain="demo"),
        )
        self.assertEqual(
            "https://demo-api.binance.com/api/v3/order",
            binance_web_utils.private_rest_url("/order", domain="demo"),
        )

    def test_demo_websocket_endpoints(self):
        self.assertEqual(
            "wss://demo-stream.binance.com:9443/ws",
            binance_web_utils.public_ws_url(domain="demo"),
        )
        self.assertEqual(
            "wss://demo-ws-api.binance.com/ws-api/v3",
            binance_web_utils.private_ws_url(domain="demo"),
        )

