# Riset Funding Rate Arbitrage BTCUSDT - Tahap 1

## Status dan batasan

- Status: riset offline saja.
- Bot produksi, controller, konfigurasi demo/paper, dan API key tidak diubah.
- Instrumen: Binance BTCUSDT spot long dan BTCUSDT USD-M perpetual short.
- Futures memakai leverage 1x dengan jaminan penuh.
- Posisi dinormalisasi ke `q` BTC yang sama pada kedua kaki. Ini membuat eksposur harga BTC mendekati delta-neutral; nilai USDT kedua kaki dapat sedikit berbeda karena basis.
- Modal yang menjadi penyebut return adalah `q * spot_entry + q * futures_entry`, yaitu biaya membeli spot ditambah jaminan penuh untuk short futures 1x. Funding APR tetap dilaporkan terhadap notional futures, sedangkan return strategi dilaporkan terhadap modal dua kaki ini.

## Data dan batas waktu

- Funding rate: arsip resmi Binance USD-M `BTCUSDT-fundingRate-YYYY-MM.zip`, yang menyediakan `fundingTime` dan `fundingRate` terealisasi.
- Arsip funding tidak memuat `markPrice`. Untuk setiap fundingTime, nilai pembayaran funding diproksikan oleh `open` mark-price kline 1 menit resmi pada menit yang memuat fundingTime. Ini adalah proksi terdokumentasi, bukan klaim harga settlement Binance yang persis.
- Harga eksekusi spot: open candle spot 1 menit.
- Harga eksekusi perpetual: open candle perpetual-futures 1 menit.
- Mark-price kline dipakai hanya untuk mengaproksimasi nilai pembayaran funding, bukan sebagai proxy fill order.
- Basis eksekusi: `futures_execution_price - spot_execution_price` pada timestamp entry dan exit yang sama.
- Basis mark: `funding_mark_price - spot_price` pada setiap fundingTime, dilaporkan terpisah sebagai statistik pasar.
- Rentang riset dimulai dari funding record BTCUSDT pertama yang berhasil diambil dan berakhir pada record terakhir yang lengkap. Rentang tidak dipaksa mundur sebelum kontrak perpetual memiliki data.
- Pagination funding wajib memakai `startTime` yang maju dari fundingTime terakhir yang telah diterima. Satu request maksimum 1.000 record.

## Prasyarat timezone sebelum Tahap 2

`Bitcoin_BTCUSDT.csv` memiliki timestamp tanpa offset. Sebelum file itu dipasangkan dengan fundingTime UTC, audit berikut wajib lulus:

1. Unduh satu bulan data spot BTCUSDT 1 menit dari arsip publik Binance beserta checksum.
2. Bandingkan seluruh nilai OHLCV bulan tersebut terhadap CSV lokal untuk offset kandidat UTC-12 sampai UTC+12.
3. Terima hanya jika terdapat satu offset unik yang membuat timestamp dan OHLCV cocok secara deterministik.
4. Konversikan timestamp CSV lokal ke UTC menggunakan offset yang terbukti.
5. Jika tidak ada offset unik, CSV lokal tidak boleh dipakai untuk riset funding. Gunakan spot data resmi yang diunduh pada rentang funding yang sama.

Tidak ada keputusan entry, exit, basis, atau funding yang boleh dihitung sebelum audit ini lulus.

## Hipotesis dan sinyal

Funding rate yang dipakai adalah funding yang sudah terealisasi. Predicted funding rate tidak dipakai.

- `APR_t = fundingRate_t * 3 * 365`.
- `rolling_apr_t` adalah rata-rata tiga funding rate terealisasi terakhir, termasuk pembayaran pada waktu `t`, dikalikan `3 * 365`.
- Keputusan hanya dibuat segera setelah funding pada waktu `t` terealisasi.
- Entry dilakukan pada open candle 1 menit pertama yang dimulai setelah `t`; funding pada `t` tidak dihitung sebagai pendapatan posisi baru.
- Hanya satu posisi boleh aktif.

Grid Tahap 4 dikunci menjadi enam pasangan berikut:

| Entry rolling APR | Exit rolling APR |
| --- | --- |
| > 5% | < 5% |
| > 5% | < 2.5% |
| > 10% | < 10% |
| > 10% | < 5% |
| > 15% | < 15% |
| > 15% | < 7.5% |

Exit juga wajib jika salah satu kondisi berikut terjadi:

- Pada fundingTime pertama yang terjadi pada atau setelah posisi berumur 90 hari kalender.
- Data funding, spot 1 menit, atau futures 1 menit yang dibutuhkan menjadi tidak lengkap selama episode. Episode tersebut tidak diberi fill sintetis dan tidak dianggap exit; episode diberi status `censored` lalu dilaporkan terpisah beserta jumlah dan waktu terjadinya. Episode censored tidak boleh diam-diam dibuang dari laporan cakupan data.

Jika sinyal exit terjadi setelah funding `t` terealisasi, exit dilakukan pada open candle 1 menit pertama setelah `t`. Funding pada `t` tetap menjadi milik posisi yang telah aktif sebelum `t`.

Urutan keputusan pada setiap fundingTime untuk posisi aktif adalah: (1) catat funding yang baru terealisasi, (2) jika batas 90 hari tercapai, exit dengan alasan `time_limit`, (3) jika tidak, cek rolling APR dan exit dengan alasan `funding_exit` bila melewati ambang exit. `time_limit` menang bila kedua kondisi exit terpenuhi pada event yang sama. Setelah exit, tidak ada re-entry pada fundingTime yang sama; peluang entry berikutnya baru dievaluasi setelah funding terealisasi berikutnya.

## Perhitungan return

Untuk satu posisi berukuran `q` BTC:

- Spot PnL: `q * (spot_exit - spot_entry)`.
- Futures short PnL: `q * (futures_entry - futures_exit)`.
- Basis PnL: `q * ((futures_entry - spot_entry) - (futures_exit - spot_exit))`.
- Funding PnL: jumlah `q * funding_mark_price * funding_rate` untuk seluruh funding selama posisi aktif. Nilai positif diterima short; nilai negatif dibayar short.
- Biaya transaksi basis: 0.10% pada setiap fill spot dan 0.05% pada setiap fill futures, semuanya diasumsikan taker. Empat fill menghasilkan biaya nominal sekitar 0.30% dari satu notional kaki, atau sekitar 0.15% dari modal dua kaki ketika basis kecil.
- Sensitivitas biaya: 0.20% total round-trip dari satu notional kaki, atau sekitar 0.10% dari modal dua kaki ketika basis kecil. Ini adalah asumsi optimistis, bukan klaim fee akun pengguna.
- Return bersih: `(spot_pnl + futures_pnl + funding_pnl - semua_fee) / modal_awal`.

Funding PnL, basis PnL, spot PnL, futures PnL, dan fee selalu dilaporkan sebagai komponen terpisah. Tidak ada komponen yang disembunyikan di dalam return total.

## Audit anti-look-ahead

- Funding untuk keputusan entry/exit hanya berasal dari record yang fundingTime-nya sudah lewat.
- Rolling average tidak boleh memasukkan rate masa depan atau predicted rate.
- Harga entry/exit selalu berasal dari candle 1 menit yang dimulai setelah waktu keputusan, bukan close candle yang belum selesai.
- Basis entry/exit memakai harga spot dan futures pada candle yang sama.
- Interval funding BTCUSDT diperiksa dari jarak antar fundingTime. Record dengan interval yang tidak sesuai atau data kosong dilaporkan, bukan diasumsikan 8 jam.

## Risiko di luar statistik return

Riset ini tidak menghapus risiko exchange/counterparty, kegagalan API, ketidakmampuan menutup dua kaki bersamaan, perubahan fee, perubahan funding interval, spread dan slippage, margin call karena harga ekstrem atau basis melebar, serta funding yang berbalik negatif ketika posisi masih aktif. Semua risiko tersebut harus tercantum lagi jika strategi sampai memasuki tahap paper trading.

Simulasi versi pertama mengasumsikan posisi 1x fully collateralized tidak dilikuidasi. Ini adalah batasan model, bukan klaim bahwa risiko likuidasi nol pada Binance. Mode margin, maintenance margin, perubahan collateral, dan harga likuidasi belum dimodelkan; seluruhnya wajib dimodelkan atau dibuktikan aman sebelum strategi dapat memasuki paper trading.

## Sanity check delta-neutral Tahap 3

- Setiap episode harus memakai kuantitas dasar `q` BTC yang sama persis pada kaki spot dan short perpetual.
- Untuk setiap entry/exit yang lengkap, `spot_pnl + futures_short_pnl` harus sama dengan `basis_pnl` hingga toleransi pembulatan numerik.
- Selisih di luar toleransi menandakan kesalahan pairing kuantitas atau timestamp. Episode tersebut tidak boleh diteruskan ke grid search sebelum penyebabnya diperbaiki dan seluruh episode dihitung ulang.
