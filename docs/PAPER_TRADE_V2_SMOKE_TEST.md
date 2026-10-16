# Paper Trade V2 Execution Smoke Test

This test verifies the narrow execution path that was previously failing:

1. `PositionExecutor` asks the strategy to place a BUY.
2. `MockPaperExchange.buy()` registers the order in the real paper connector
   `_order_tracker`.
3. BUY created, filled, and completed events are delivered to the executor.
4. The executor places a SELL close order through the same strategy path.
5. SELL created, filled, and completed events are delivered to the executor.

The test is deliberately isolated. It uses `MockPaperExchange`, a synthetic
pair, and synthetic events. It does not read or write exchange credentials,
the live/paper launcher, the strategy YAML, the client password, the SQLite
database, or production logs. It also does not change signal filters.

Run only this smoke test from PowerShell:

```powershell
C:\Users\User\miniconda3\Scripts\conda.exe run -n hummingbot --no-capture-output pytest -q test/hummingbot/strategy_v2/executors/position_executor/test_paper_trade_position_lifecycle.py
```

A passing result proves the BUY/SELL tracker and executor event hand-off in
the current Python environment. It does not prove Binance connectivity or a
profitable strategy signal; those are separate runtime concerns.

