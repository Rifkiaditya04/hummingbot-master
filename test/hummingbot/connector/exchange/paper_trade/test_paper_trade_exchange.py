from unittest import TestCase
from decimal import Decimal

from hummingbot.connector.exchange.binance.binance_api_order_book_data_source import BinanceAPIOrderBookDataSource
from hummingbot.connector.exchange.kucoin.kucoin_api_order_book_data_source import KucoinAPIOrderBookDataSource
from hummingbot.connector.exchange.paper_trade import create_paper_trade_market, get_order_book_tracker
from hummingbot.connector.test_support.mock_paper_exchange import MockPaperExchange
from hummingbot.core.data_type.common import OrderType
from hummingbot.core.data_type.order_book_tracker import OrderBookTracker


class PaperTradeExchangeTests(TestCase):

    def test_get_order_book_tracker_for_connector_using_generic_tracker(self):
        tracker = get_order_book_tracker(connector_name="binance", trading_pairs=["COINALPHA-HBOT"])
        self.assertEqual(OrderBookTracker, type(tracker))

        tracker = get_order_book_tracker(connector_name="kucoin", trading_pairs=["COINALPHA-HBOT"])
        self.assertEqual(OrderBookTracker, type(tracker))

    def test_create_paper_trade_market_for_connector_using_generic_tracker(self):
        paper_exchange = create_paper_trade_market(
            exchange_name="binance",
            trading_pairs=["COINALPHA-HBOT"])
        self.assertEqual(BinanceAPIOrderBookDataSource, type(paper_exchange.order_book_tracker.data_source))

        paper_exchange = create_paper_trade_market(
            exchange_name="kucoin",
            trading_pairs=["COINALPHA-HBOT"])
        self.assertEqual(KucoinAPIOrderBookDataSource, type(paper_exchange.order_book_tracker.data_source))

    def test_paper_trade_market_exposes_v2_trading_rules_contract(self):
        paper_exchange = MockPaperExchange()
        paper_exchange.new_empty_order_book("COINALPHA-HBOT")

        self.assertTrue(hasattr(paper_exchange, "trading_rules"))
        self.assertIn("COINALPHA-HBOT", paper_exchange.trading_rules)

    def test_paper_trade_market_tracks_v2_orders(self):
        paper_exchange = MockPaperExchange()
        paper_exchange.new_empty_order_book("COINALPHA-HBOT")

        order_id = paper_exchange.buy(
            "COINALPHA-HBOT", Decimal("1"), order_type=OrderType.MARKET
        )

        tracked_order = paper_exchange._order_tracker.fetch_order(client_order_id=order_id)
        self.assertIsNotNone(tracked_order)
        self.assertEqual(order_id, tracked_order.client_order_id)
