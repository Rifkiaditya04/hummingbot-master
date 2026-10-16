# Paper Trade V2 Order Tracking

## Problem

`PositionExecutor` resolves order IDs through the connector's `_order_tracker`.
The Cython `PaperTradeExchange` previously emitted created, filled, and completed
events without exposing that V2 contract. A paper BUY could therefore fill while
the executor raised `AttributeError` during event handling.

## Implementation

`PaperTradeExchange` now owns a small in-memory tracker that:

- registers paper orders when `buy()` or `sell()` creates them;
- exposes `fetch_order(client_order_id=...)` to V2 executors;
- records each paper fill as a `TradeUpdate` before forwarding the fill event;
- marks the tracked order as `FILLED` after its simulated fill.

The tracker is simulation-only and does not affect live Binance connectors.

## Verification

The regression test must verify that a paper market order is retrievable through
`paper_exchange._order_tracker`. The Cython extension must be rebuilt after
changing `paper_trade_exchange.pyx` or its `.pxd` file.

Passing this test confirms the connector contract; a fresh paper run is still
required to confirm the complete executor lifecycle and P&L in the UI/log.
