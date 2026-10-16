# Paper Trade V2 Execution Fix

## Evidence

The BTC-USDT paper run emitted `[HCM] EXEC BUY`, then failed while constructing
`PositionExecutor` because `PaperTradeExchange` had no `trading_rules`
attribute. No order submission or fill event was reached.

The V2 executor contract reads `connector.trading_rules[trading_pair]`.
Paper trade is a Cython connector that initializes order books and simulates
fills locally, so it does not request live exchange trading rules.

## Implementation

`PaperTradeExchange.trading_rules` now returns a virtual `TradingRule` for each
initialized paper trading pair. The rule uses the connector's default
simulation constraints and does not change Binance live connector behavior.

A regression test verifies that the paper connector exposes the V2 contract.
The Cython extension must be rebuilt before the launcher can load this change.

## Verification criteria

After rebuilding and restarting paper trade, the log must show no
`PaperTradeExchange ... has no attribute 'trading_rules'` errors. A successful
run should progress from one `[HCM] EXEC BUY` entry to paper order and fill
events, without repeating the same action every second.

This fix makes execution possible; it does not guarantee profitability or
validate the strategy's trading edge.
