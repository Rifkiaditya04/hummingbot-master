# Riset Funding Rate Arbitrage BTCUSDT - Tahap 2

## Status

- Status: checkpoint sebelum Tahap 3. Tidak ada simulasi posisi atau perubahan bot produksi.
- Cakupan data: 2020-01-01 00:00 UTC sampai 2026-08-31 16:00:00.001 UTC.
- Sumber harga: 80 arsip bulanan resmi Binance untuk spot, perpetual futures, dan mark-price kline 1 menit.
- Sumber funding: 7.305 funding record BTCUSDT terealisasi dengan interval deklaratif delapan jam.

## Evidence data

- Price-event pairing lengkap untuk 7.274 dari 7.305 funding event; 31 event (0,424%) ditandai `censored` karena harga spot atau mark pada menit yang diperlukan tidak tersedia. Tidak ada harga pengganti atau fill sintetis.
- Timestamp spot berubah dari milidetik menjadi mikrodetik pada 20 arsip mulai 2025-01. Audit menormalkannya ke milidetik hanya setelah memastikan semua timestamp tetap sejajar menit. Ini adalah perbedaan format, bukan perubahan waktu pasar.
- Futures memiliki nol gap satu menit. Setelah normalisasi timestamp, spot memiliki 15 gap dan mark-price memiliki 9 gap. Dampaknya sudah tercakup dalam 31 event `censored`.
- Mark price settlement persis tidak tersedia di arsip funding. Funding PnL Tahap 3 kelak memakai `open` mark-price kline pada menit funding sebagai proksi yang telah dikunci pada Tahap 1. Ini adalah keterbatasan model, bukan harga settlement yang diklaim persis.

Artefak yang dapat diaudit:

- `data/research/funding_rate_arbitrage/funding_price_events.csv`
- `data/research/funding_rate_arbitrage/funding_price_join_audit.json`
- `data/research/funding_rate_arbitrage/price_coverage_audit.json`
- `data/research/funding_rate_arbitrage/funding_stage2_baseline.json`

## Baseline funding

| Metrik | Seluruh data | Sejak 2023 |
| --- | ---: | ---: |
| Funding positif | 85,886% | 86,258% |
| Funding negatif | 14,114% | 13,742% |
| Median APR funding terealisasi | 10,161% | 6,753% |
| Median rolling APR 3 funding | 8,214% | 6,328% |
| Gross funding APR berkelanjutan terhadap futures notional | 11,798% | 7,276% |
| Gross funding APR berkelanjutan terhadap modal dua kaki | 5,899% | 3,638% |

Durasi episode rolling APR sejak 2023:

| Ambang entry | Jumlah episode | Median | P75 | Maksimum |
| --- | ---: | ---: | ---: | ---: |
| > 5% APR | 200 | 32 jam | 64 jam | 2.616 jam |
| > 10% APR | 87 | 24 jam | 60 jam | 1.568 jam |
| > 15% APR | 24 | 52 jam | 86 jam | 464 jam |

## Basis

Basis eksekusi didefinisikan sebagai `futures_open - spot_open` pada menit sesudah funding event.

| Persentil | Basis eksekusi |
| --- | ---: |
| P10 | -0,0579% |
| P25 | -0,0494% |
| P50 | -0,0375% |
| P75 | 0,0091% |
| P90 | 0,0774% |

Untuk long spot dan short perpetual, basis PnL adalah `basis_entry - basis_exit`. Karena itu, premium futures positif pada entry yang kemudian menyempit menuju nol menguntungkan; futures diskon pada entry yang naik menuju nol justru merugikan. Ini mengoreksi intuisi arah basis yang keliru dan akan dihitung terpisah dari funding pada Tahap 4.

## Checkpoint biaya wajib

Model biaya yang dikunci di Tahap 1 mengasumsikan empat taker fill dengan total sekitar 0,30% dari satu notional kaki, atau 0,15% dari modal dua-kaki ketika basis kecil.

- Dengan rata-rata funding berkelanjutan sejak 2023, biaya tersebut secara aritmetika baru impas setelah sekitar 15,05 hari hold.
- Episode threshold tipikal hanya bertahan 1 sampai 2 hari, jauh lebih pendek dari 15,05 hari.
- Angka ini belum memasukkan funding negatif saat posisi aktif, basis entry/exit, spread, slippage, censoring, atau turnover nyata.

## Interpretasi dan keputusan gerbang

Evidence menunjukkan data cukup untuk mensimulasikan strategi, tetapi juga menunjukkan red flag ekonomi: income funding tipikal pada episode singkat kemungkinan tidak menutup biaya empat fill. Ini belum membuktikan strategi gagal karena Tahap 3 dan 4 belum menghitung income setiap episode, basis PnL, atau exit aktual.

Sesuai perintah riset, Tahap 3 tidak dijalankan sebelum checkpoint ini dilaporkan dan ada keputusan eksplisit untuk melanjutkan. Tidak ada kesimpulan edge positif maupun perubahan bot dari Tahap 2.
