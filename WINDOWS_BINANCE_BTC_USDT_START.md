# Windows Binance BTC-USDT Start

Tujuan baseline ini:
- Windows + PowerShell friendly
- Binance paper trade
- Pair awal `BTC-USDT`
- Bot hanya entry saat sinyal cukup ketat
- Default `long_only`

## File penting

- `install.ps1`: install environment untuk Windows
- `start.ps1`: entrypoint PowerShell umum
- `run-binance-btc-usdt-paper.ps1`: shortcut untuk baseline awal
- `conf/controllers/binance_btc_usdt_high_conf.yml`: aturan controller utama
- `conf/scripts/binance_btc_usdt_high_conf_bot.yml`: script config V2
- `controllers/directional_trading/high_confidence_momentum.py`: controller sinyal selektif

## Alur start

```powershell
.\install.ps1
.\run-binance-btc-usdt-paper.ps1
```

Atau langsung:

```powershell
.\start.ps1 -V2 binance_btc_usdt_high_conf_bot.yml
```

## Karakter strategi awal

- Connector default: `binance_paper_trade`
- Pair default: `BTC-USDT`
- Side default: `long_only`
- Timeframe default: `5m`
- Bot butuh beberapa konfirmasi sekaligus sebelum entry

Konfirmasi utama:
- trend EMA cepat di atas EMA lambat
- harga reclaim EMA cepat
- RSI cukup kuat tapi belum terlalu overbought
- ADX di atas ambang minimum
- ATR tidak terlalu kecil dan tidak terlalu liar
- volume di atas rata-rata
- posisi Bollinger band masih masuk area entry

Kalau syarat tidak bersih, bot akan diam.

## Parameter awal yang penting

File: `conf/controllers/binance_btc_usdt_high_conf.yml`

- `total_amount_quote`: modal simulasi per sinyal
- `cooldown_time`: jeda minimal antar-entry
- `stop_loss`: batas rugi
- `take_profit`: target ambil untung
- `time_limit`: batas waktu posisi
- `trade_side_mode`: `long_only`, `short_only`, atau `both`
- `min_confirmation_count`: makin tinggi makin selektif

## Cara bikin bot lebih ketat

Naikkan salah satu atau beberapa:
- `min_confirmation_count`
- `adx_threshold`
- `min_volume_ratio`
- `cooldown_time`
- `rsi_long_threshold`

Turunkan agresivitas entry dengan mempersempit:
- `bb_long_min`
- `bb_long_max`

## Catatan

- Baseline ini sengaja dibuat konservatif, bukan high-frequency.
- Karena memakai `binance_paper_trade`, belum ada order live ke Binance.
- Setelah perilaku bot sudah stabil di paper trade, baru kita pindahkan ke connector live.
