from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock

from test.isolated_asyncio_wrapper_test_case import IsolatedAsyncioWrapperTestCase

from hummingbot.connector.test_support.mock_paper_exchange import MockPaperExchange
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.data_type.trade_fee import AddedToCostTradeFee, TokenAmount
from hummingbot.core.event.events import (
    BuyOrderCompletedEvent,
    BuyOrderCreatedEvent,
    OrderFilledEvent,
    SellOrderCompletedEvent,
    SellOrderCreatedEvent,
)
from hummingbot.strategy.strategy_v2_base import StrategyV2Base
from hummingbot.strategy_v2.executors.position_executor.data_types import (
    PositionExecutorConfig,
    TripleBarrierConfig,
)
from hummingbot.strategy_v2.executors.position_executor.position_executor import PositionExecutor
from hummingbot.strategy_v2.models.executors import CloseType


class TestPaperTradePositionLifecycle(IsolatedAsyncioWrapperTestCase):
    """Deterministic BUY -> SELL smoke test for the V2 paper execution path."""

    pair = "COINALPHA-HBOT"
    connector_name = "mock_paper_exchange"
    timestamp = 1_700_000_000
    amount = Decimal("1")
    price = Decimal("100")

    def setUp(self):
        super().setUp()
        self.exchange = MockPaperExchange()
        self.exchange.new_empty_order_book(self.pair)

        self.strategy = MagicMock(spec=StrategyV2Base)
        self.strategy.connectors = {self.connector_name: self.exchange}
        type(self.strategy).current_timestamp = PropertyMock(return_value=self.timestamp)
        self.strategy.cancel.return_value = None
        self.strategy.buy.side_effect = self._buy
        self.strategy.sell.side_effect = self._sell

    def _buy(self, connector_name, trading_pair, amount, order_type, price, position_action):
        return self.exchange.buy(trading_pair, amount, order_type=order_type, price=price)

    def _sell(self, connector_name, trading_pair, amount, order_type, price, position_action):
        return self.exchange.sell(trading_pair, amount, order_type=order_type, price=price)

    def _config(self):
        return PositionExecutorConfig(
            id="paper-lifecycle-smoke",
            timestamp=self.timestamp,
            trading_pair=self.pair,
            connector_name=self.connector_name,
            side=TradeType.BUY,
            entry_price=self.price,
            amount=self.amount,
            triple_barrier_config=TripleBarrierConfig(
                stop_loss=Decimal("0.05"),
                take_profit=Decimal("0.05"),
                time_limit=60,
                take_profit_order_type=OrderType.MARKET,
                stop_loss_order_type=OrderType.MARKET,
            ),
        )

    def _fee(self):
        return AddedToCostTradeFee(
            flat_fees=[TokenAmount(token="HBOT", amount=Decimal("0"))]
        )

    def test_buy_then_sell_updates_position_executor_without_tracker_errors(self):
        executor = PositionExecutor(self.strategy, self._config())

        # BUY: the strategy routes the order to the real paper connector tracker.
        executor.place_open_order()
        buy_id = executor._open_order.order_id
        buy_order = self.exchange._order_tracker.fetch_order(client_order_id=buy_id)
        self.assertIsNotNone(buy_order)
        executor.process_order_created_event(
            None,
            self.exchange,
            BuyOrderCreatedEvent(
                self.timestamp, OrderType.MARKET, self.pair, self.amount,
                self.price, buy_id, self.timestamp,
            ),
        )
        buy_fill = OrderFilledEvent(
            self.timestamp + 1,
            buy_id,
            self.pair,
            TradeType.BUY,
            OrderType.MARKET,
            self.price,
            self.amount,
            self._fee(),
            exchange_trade_id="smoke-buy-fill",
        )
        self.exchange._order_tracker.record_fill(buy_fill)
        executor.process_order_filled_event(None, self.exchange, buy_fill)
        executor.process_order_completed_event(
            None,
            self.exchange,
            BuyOrderCompletedEvent(
                self.timestamp + 1, buy_id, "COINALPHA", "HBOT",
                self.amount, self.amount * self.price, OrderType.MARKET,
            ),
        )
        self.assertEqual(executor.open_filled_amount, self.amount)

        # SELL: close the same position through the normal executor order path.
        executor.place_close_order_and_cancel_open_orders(CloseType.TAKE_PROFIT)
        sell_id = executor._close_order.order_id
        sell_order = self.exchange._order_tracker.fetch_order(client_order_id=sell_id)
        self.assertIsNotNone(sell_order)
        executor.process_order_created_event(
            None,
            self.exchange,
            SellOrderCreatedEvent(
                self.timestamp + 2, OrderType.MARKET, self.pair, self.amount,
                self.price, sell_id, self.timestamp + 2,
            ),
        )
        sell_fill = OrderFilledEvent(
            self.timestamp + 3,
            sell_id,
            self.pair,
            TradeType.SELL,
            OrderType.MARKET,
            self.price,
            self.amount,
            self._fee(),
            exchange_trade_id="smoke-sell-fill",
        )
        self.exchange._order_tracker.record_fill(sell_fill)
        executor.process_order_filled_event(None, self.exchange, sell_fill)
        executor.process_order_completed_event(
            None,
            self.exchange,
            SellOrderCompletedEvent(
                self.timestamp + 3, sell_id, "COINALPHA", "HBOT",
                self.amount, self.amount * self.price, OrderType.MARKET,
            ),
        )

        self.assertEqual(executor.close_filled_amount, self.amount)
        self.assertEqual(executor._total_executed_amount_backup, self.amount * 2)
