# Binance Spot Demo Setup

The normal paper launcher remains unchanged. The Demo launcher uses the
dedicated `binance_demo` connector and Binance Demo endpoints.

## Before connecting

The API key and secret previously pasted into chat must be revoked. Create a
new Demo Spot key and keep both values local. Never put them in this file, a
PowerShell script, a screenshot, or Git.

## Store credentials safely

From the project directory, start an interactive Hummingbot session without
the live preflight:

```powershell
cd D:\Crypto\hummingbot-master
.\start.ps1 -SkipPreflight
```

At the `>>>` prompt, run:

```text
connect binance_demo
```

Enter the new Demo API key and secret when prompted. Hummingbot stores them in
its encrypted connector configuration. Then run:

```text
exit
```

Do not paste the credentials into the terminal command line because they can
remain in shell history or process listings.

## Run Demo Spot

```powershell
cd D:\Crypto\hummingbot-master
.\run-binance-btc-usdt-demo.ps1
```

This launcher performs a Demo REST and WebSocket preflight before starting
`binance_btc_usdt_high_conf_demo.yml`. To debug a known network-check issue:

```powershell
.\run-binance-btc-usdt-demo.ps1 -SkipPreflight
```

The Demo controller intentionally keeps the current strategy parameters. It
does not alter the paper controller or its launcher.

## Verification scope

The first runtime verification should be performed in this order:

1. Demo REST time and exchange information.
2. Authenticated Demo account balance.
3. A controlled minimum-size BUY.
4. The matching SELL close.
5. Only then, the full selective strategy.

The Demo environment is separate from live trading, but its API key must still
be treated as a secret.

