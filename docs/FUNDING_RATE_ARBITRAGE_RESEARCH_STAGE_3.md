# Riset Funding Rate Arbitrage BTCUSDT - Tahap 3

## Status dan batasan

- Status: simulasi offline enam kombinasi yang dikunci pada Tahap 1.
- Bot demo/paper, controller, konfigurasi, API key, dan kode produksi tidak dibaca untuk eksekusi dan tidak diubah.
- Rentang data: 2020-01 sampai 2026-08. Tahap ini tidak menghitung confidence interval, optimasi tambahan, atau walk-forward.
- Hasil tertutup pada Tahap 3 untuk review sebelum Tahap 4.

## Definisi yang dikunci sebelum data dijalankan

### Basis APR threshold

- Threshold entry dan exit `5%`, `10%`, serta `15%` memakai APR terhadap **futures notional**. Rumusnya: `rolling_average_3_funding_rate * 3 * 365 * 100`.
- Untuk modal dua-kaki dengan nilai spot dan futures setara, ekuivalennya kira-kira separuh: `5% -> 2,5%`, `10% -> 5,0%`, `15% -> 7,5%` APR terhadap modal dua-kaki.
- Ekuivalen tepat per episode adalah `APR_futures_notional * futures_entry / (spot_entry + futures_entry)`. Nilai ini dilaporkan pada ledger; tidak digunakan untuk mengubah atau menyaring sinyal.
- Enam kombinasi tetap: `5/5`, `5/2,5`, `10/10`, `10/5`, `15/15`, `15/7,5` dengan format `entry/exit` dalam APR futures notional.

### Urutan resolusi pada funding event

Untuk posisi yang telah aktif sebelum funding event `t`:

1. Jika data mark/spot/futures yang diperlukan pada `t` atau pada open satu menit setelah `t` tidak lengkap, event dan episode diberi penanda `censored`; tidak ada harga pengganti dan tidak ada fee exit sintetis.
2. Jika data lengkap, funding pada `t` dicatat terlebih dahulu karena posisi sudah aktif sebelum pembayaran tersebut.
3. Jika usia posisi telah mencapai 90 hari pada `t`, posisi menerima alasan exit `time_limit`.
4. Jika tidak terkena `time_limit` dan rolling APR terealisasi berada di bawah threshold exit, posisi menerima alasan exit `funding_exit`.
5. `time_limit` menang atas `funding_exit` pada event yang sama. Setelah exit, tidak ada re-entry pada event yang sama; evaluasi entry baru dimulai pada funding event berikutnya.

Jika gap terjadi ketika posisi aktif tetapi event berikutnya lengkap, status episode tetap `censored`; state posisi tetap mengikuti sinyal nyata sampai exit terobservasi atau akhir data. Ledger episode censored tidak diberi total net return yang dipalsukan. Jika keputusan exit terjadi pada event dengan harga eksekusi yang hilang, waktu dan alasan exit dicatat, tetapi seluruh episode tetap censored tanpa fill buatan.

### Margin dan risiko yang tidak dimodelkan

- Simulasi memakai long spot dan short perpetual sebesar `q` BTC yang sama, leverage futures 1x, dan fully collateralized.
- Simulasi **tidak memodelkan likuidasi**, maintenance margin, perubahan collateral, auto-deleveraging, atau risiko exchange. Ini keterbatasan riset, bukan klaim bahwa risiko tersebut nol.

### Harga dan anti-look-ahead

- Sinyal hanya memakai funding yang sudah terealisasi hingga event `t`, termasuk rolling tiga funding terakhir.
- Entry dan exit memakai open candle spot serta futures satu menit pertama setelah funding event yang memicu keputusan.
- Funding saat entry tidak dihitung sebagai pendapatan posisi baru; funding pada event exit tetap milik posisi lama.
- Funding menggunakan proksi `open` mark-price kline pada menit funding sesuai Tahap 1.

## Kill rule terkunci

Pada window sejak 2023, strategi threshold funding ditandai gagal dan Tahap 4-5 dilewati jika salah satu kondisi berikut terpenuhi pada episode non-censored:

1. Keenam kombinasi memiliki total net return `<= 0`; atau
2. Tidak ada kombinasi yang memiliki total net return tahunan lebih tinggi daripada benchmark carry selalu-hold pada tahun yang sama.

Kill rule hanya menentukan kelanjutan program riset setelah angka Tahap 3 selesai. Tahap ini tidak menyimpulkan edge positif atau negatif sebelum seluruh ledger, censoring, dan sanity check dilaporkan.

## Artefak Tahap 3 yang direncanakan

- Ledger per episode dan ringkasan hanya ditulis di `data/research/funding_rate_arbitrage/`.
- Harness sementara juga berada di folder riset tersebut dan dihapus setelah hasil terverifikasi.
- Laporan akhir Tahap 3 akan mencantumkan seluruh file yang dibuat/diubah dan semua perintah yang dijalankan.

## Koreksi implementasi pra-hasil

- Parser `entry_trigger_time_utc` pada runner memakai `pd.to_datetime(..., utc=True, format="ISO8601")` dan assertion bahwa hasilnya tidak mengandung `NaT`. Koreksi ini dilakukan sebelum menjalankan data historis agar timestamp ISO8601 dengan presisi pecahan detik diproses konsisten tanpa `format="mixed"`.
- Runner menambahkan `annual_return_recycled_capital_pct_complete`: jumlah `net_return_pct` seluruh episode complete pada subset. Metrik ini merepresentasikan asumsi satu posisi aktif dan modal didaur ulang antar-episode, sementara periode modal menganggur tidak menghasilkan return.
- `aggregate_net_return_pct_complete` tetap dipertahankan sebagai return agregat terhadap total initial capital episode. Untuk kondisi (b) kill rule, runner membandingkan metrik modal-didaur-ulang milik strategi dengan `aggregate_net_return_pct_complete` benchmark selalu-hold pada tahun yang sama; keduanya sekarang merupakan return untuk horizon tahunan yang setara secara definisi.
- Bukti definisi engine: `tmp_stage3_ledger_engine.py` baris 141-143 menghitung `total_net` sesudah spot PnL, futures PnL, funding, dan fee; lalu mendefinisikan `net_return_pct = total_net / position["initial_capital_usdt"] * 100`. Jadi `net_return_pct` adalah return net terhadap initial capital episode tersebut.

## Hasil eksekusi offline

- Input: 7.305 funding event, dari `2020-01-01 00:00:00 UTC` sampai `2026-08-31 16:00:00.001 UTC`.
- Semua angka uang memakai notional `q=1 BTC` dan hanya menghitung episode berstatus `complete`. Kolom episode tetap menampilkan seluruh episode yang terbentuk; kolom censored adalah episode yang tidak diberi fill sintetis.
- `Return modal daur ulang` adalah jumlah `net_return_pct` episode complete pada subset, sesuai asumsi satu posisi aktif dan modal didaur ulang. Ini bukan annualisasi matematis dari return rata-rata episode.
- Tanda `-` berarti metrik tidak tersedia. Untuk kombinasi/tahun tanpa episode, tabel menulis `tidak ada episode`, bukan nol.

### Definisi net return yang terkonfirmasi di engine

Pada `tmp_stage3_ledger_engine.py` baris 141-143, engine mendefinisikan:

```python
total_net = spot_pnl + futures_pnl + position["funding_pnl_observed_usdt"] - total_fee
result["net_return_pct"] = total_net / position["initial_capital_usdt"] * 100
```

Jadi `net_return_pct` adalah total net setelah funding dan fee empat fill, dibagi `initial_capital_usdt` untuk episode tersebut. Fee empat fill berasal dari buka/tutup kaki spot dan buka/tutup kaki futures sesuai definisi Tahap 1.

### Sanity check dan anti-look-ahead

- Delta-neutral: `passed`. Untuk setiap baris ledger complete, `spot_pnl + futures_pnl` sama dengan `basis_pnl` dalam toleransi engine.
- Audit anti-look-ahead: `passed_by_construction`. Sinyal menggunakan rolling mean dari funding yang telah terealisasi pada event saat ini dan dua event sebelumnya; entry/exit memakai open spot dan futures satu menit setelah event pemicu; funding event entry dikecualikan, sedangkan funding event exit tetap dihitung untuk posisi lama.

### Seluruh data tersedia (2020-01 s.d. 2026-08)

| Kombinasi | Episode | Censored | Durasi median/rata-rata jam | Funding gross USDT | Fee USDT | Basis PnL USDT | Net per episode mean/median % | Return modal daur ulang % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| entry_5_exit_5 | 326 | 8 | 32.0 / 99.5 | 21245.53 | 49956.17 | 1353.07 | -0.063 / -0.135 | -20.013 |
| entry_5_exit_2_5 | 194 | 9 | 64.0 / 167.1 | 19077.99 | 26556.77 | 987.08 | -0.021 / -0.127 | -3.856 |
| entry_10_exit_10 | 176 | 5 | 24.0 / 114.8 | 16144.64 | 23631.35 | 1456.08 | -0.019 / -0.126 | -3.226 |
| entry_10_exit_5 | 113 | 8 | 64.0 / 224.6 | 17861.22 | 12900.22 | 929.81 | 0.078 / -0.104 | 8.082 |
| entry_15_exit_15 | 78 | 3 | 48.0 / 105.4 | 18683.32 | 9195.76 | 998.86 | 0.187 / -0.055 | 14.044 |
| entry_15_exit_7_5 | 15 | 3 | 836.0 / 874.0 | 11151.90 | 1203.23 | 479.55 | 1.093 / 0.941 | 13.121 |

### Sejak 2023

| Kombinasi | Episode | Censored | Durasi median/rata-rata jam | Funding gross USDT | Fee USDT | Basis PnL USDT | Net per episode mean/median % | Return modal daur ulang % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| entry_5_exit_5 | 199 | 1 | 32.0 / 93.4 | 14745.49 | 40786.48 | 763.02 | -0.077 / -0.136 | -15.158 |
| entry_5_exit_2_5 | 100 | 2 | 72.0 / 202.1 | 15138.30 | 19839.76 | 411.31 | -0.002 / -0.128 | -0.240 |
| entry_10_exit_10 | 86 | 0 | 24.0 / 114.7 | 10262.19 | 16239.72 | 848.50 | -0.028 / -0.129 | -2.415 |
| entry_10_exit_5 | 48 | 1 | 84.0 / 265.9 | 11685.27 | 8200.18 | 454.57 | 0.103 / -0.100 | 4.747 |
| entry_15_exit_15 | 24 | 0 | 52.0 / 86.7 | 4504.40 | 4215.78 | 346.76 | 0.023 / -0.058 | 0.560 |
| entry_15_exit_7_5 | 6 | 0 | 936.0 / 925.3 | 6848.46 | 768.20 | 271.71 | 1.051 / 0.775 | 6.309 |

### Tahun 2020

| Kombinasi | Episode | Censored | Durasi median/rata-rata jam | Funding gross USDT | Fee USDT | Basis PnL USDT | Net per episode mean/median % | Return modal daur ulang % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| entry_5_exit_5 | 28 | 2 | 32.0 / 189.5 | 1237.97 | 725.16 | 91.28 | 0.089 / -0.126 | 2.322 |
| entry_5_exit_2_5 | 21 | 2 | 40.0 / 221.5 | 814.83 | 497.02 | 50.06 | 0.097 / -0.127 | 1.849 |
| entry_10_exit_10 | 20 | 2 | 88.0 / 240.9 | 1209.46 | 562.46 | 117.18 | 0.192 / -0.072 | 3.459 |
| entry_10_exit_5 | 17 | 2 | 56.0 / 304.5 | 1219.24 | 459.08 | 110.52 | 0.255 / -0.096 | 3.822 |
| entry_15_exit_15 | 27 | 2 | 48.0 / 97.9 | 2963.09 | 957.85 | 147.66 | 0.182 / -0.032 | 4.558 |
| entry_15_exit_7_5 | 6 | 2 | 640.0 / 682.0 | 998.15 | 139.93 | 46.62 | 0.961 / 0.762 | 3.843 |

### Tahun 2021

| Kombinasi | Episode | Censored | Durasi median/rata-rata jam | Funding gross USDT | Fee USDT | Basis PnL USDT | Net per episode mean/median % | Return modal daur ulang % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| entry_5_exit_5 | 21 | 3 | 28.0 / 240.4 | 4296.42 | 2012.91 | 130.32 | 0.115 / -0.126 | 2.064 |
| entry_5_exit_2_5 | 19 | 3 | 20.0 / 179.5 | 2260.10 | 1773.86 | 251.06 | 0.029 / -0.121 | 0.460 |
| entry_10_exit_10 | 20 | 2 | 48.0 / 202.2 | 4056.77 | 2307.58 | 177.44 | 0.094 / -0.104 | 1.688 |
| entry_10_exit_5 | 11 | 3 | 64.0 / 508.0 | 4243.33 | 971.09 | 82.20 | 0.401 / -0.116 | 3.211 |
| entry_15_exit_15 | 27 | 1 | 44.0 / 129.8 | 11215.82 | 4022.13 | 504.44 | 0.343 / -0.067 | 8.926 |
| entry_15_exit_7_5 | 3 | 1 | 1104.0 / 1104.0 | 3305.29 | 295.10 | 161.22 | 1.485 / 1.485 | 2.970 |

### Tahun 2022

| Kombinasi | Episode | Censored | Durasi median/rata-rata jam | Funding gross USDT | Fee USDT | Basis PnL USDT | Net per episode mean/median % | Return modal daur ulang % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| entry_5_exit_5 | 78 | 2 | 24.0 / 51.1 | 965.65 | 6431.62 | 368.45 | -0.122 / -0.135 | -9.240 |
| entry_5_exit_2_5 | 54 | 2 | 56.0 / 78.2 | 864.76 | 4446.12 | 274.65 | -0.114 / -0.127 | -5.924 |
| entry_10_exit_10 | 50 | 1 | 16.0 / 36.4 | 616.22 | 4521.59 | 312.96 | -0.122 / -0.130 | -5.958 |
| entry_10_exit_5 | 37 | 2 | 56.0 / 71.3 | 713.38 | 3269.88 | 282.52 | -0.106 / -0.116 | -3.697 |
| entry_15_exit_15 | tidak ada episode | - | - | - | - | - | - | - |
| entry_15_exit_7_5 | tidak ada episode | - | - | - | - | - | - | - |

### Tahun 2023

| Kombinasi | Episode | Censored | Durasi median/rata-rata jam | Funding gross USDT | Fee USDT | Basis PnL USDT | Net per episode mean/median % | Return modal daur ulang % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| entry_5_exit_5 | 55 | 1 | 36.0 / 110.8 | 2498.19 | 4313.78 | 74.65 | -0.064 / -0.136 | -3.460 |
| entry_5_exit_2_5 | 31 | 1 | 84.0 / 197.9 | 2374.81 | 2419.08 | 7.64 | -0.013 / -0.124 | -0.397 |
| entry_10_exit_10 | 32 | 0 | 20.0 / 128.3 | 2153.23 | 2669.46 | 164.40 | -0.039 / -0.134 | -1.250 |
| entry_10_exit_5 | 21 | 1 | 40.0 / 224.4 | 2200.36 | 1654.68 | 75.75 | 0.040 / -0.128 | 0.799 |
| entry_15_exit_15 | 10 | 0 | 36.0 / 60.8 | 720.06 | 1013.96 | 129.70 | -0.041 / -0.081 | -0.413 |
| entry_15_exit_7_5 | 4 | 0 | 424.0 / 742.0 | 1754.47 | 336.75 | 141.20 | 0.574 / 0.189 | 2.296 |

### Tahun 2024

| Kombinasi | Episode | Censored | Durasi median/rata-rata jam | Funding gross USDT | Fee USDT | Basis PnL USDT | Net per episode mean/median % | Return modal daur ulang % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| entry_5_exit_5 | 28 | 0 | 36.0 / 231.7 | 7762.89 | 5250.79 | 225.24 | 0.106 / -0.131 | 2.964 |
| entry_5_exit_2_5 | 16 | 0 | 72.0 / 428.0 | 7861.05 | 3051.61 | 152.48 | 0.324 / -0.122 | 5.185 |
| entry_10_exit_10 | 25 | 0 | 32.0 / 183.7 | 6676.49 | 5103.65 | 325.40 | 0.094 / -0.118 | 2.342 |
| entry_10_exit_5 | 9 | 0 | 392.0 / 630.2 | 7392.24 | 1653.59 | 155.40 | 0.598 / 0.074 | 5.383 |
| entry_15_exit_15 | 14 | 0 | 68.0 / 105.1 | 3784.34 | 3201.83 | 217.06 | 0.069 / -0.049 | 0.973 |
| entry_15_exit_7_5 | 2 | 0 | 1292.0 / 1292.0 | 5093.98 | 431.45 | 130.51 | 2.006 / 2.006 | 4.012 |

### Tahun 2025

| Kombinasi | Episode | Censored | Durasi median/rata-rata jam | Funding gross USDT | Fee USDT | Basis PnL USDT | Net per episode mean/median % | Return modal daur ulang % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| entry_5_exit_5 | 75 | 0 | 24.0 / 56.0 | 3652.90 | 22263.59 | 382.90 | -0.124 / -0.136 | -9.311 |
| entry_5_exit_2_5 | 37 | 0 | 72.0 / 148.5 | 4305.46 | 11044.24 | 234.11 | -0.091 / -0.127 | -3.352 |
| entry_10_exit_10 | 22 | 0 | 16.0 / 45.8 | 1307.10 | 6945.18 | 271.52 | -0.118 / -0.134 | -2.598 |
| entry_10_exit_5 | 14 | 0 | 108.0 / 126.3 | 1928.92 | 4303.94 | 200.70 | -0.081 / -0.098 | -1.131 |
| entry_15_exit_15 | tidak ada episode | - | - | - | - | - | - | - |
| entry_15_exit_7_5 | tidak ada episode | - | - | - | - | - | - | - |

### Tahun 2026 (sampai 2026-08-31)

| Kombinasi | Episode | Censored | Durasi median/rata-rata jam | Funding gross USDT | Fee USDT | Basis PnL USDT | Net per episode mean/median % | Return modal daur ulang % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| entry_5_exit_5 | 41 | 0 | 28.0 / 43.4 | 831.51 | 8958.32 | 80.23 | -0.134 / -0.139 | -5.350 |
| entry_5_exit_2_5 | 16 | 1 | 40.0 / 94.3 | 596.98 | 3324.83 | 17.08 | -0.120 / -0.142 | -1.676 |
| entry_10_exit_10 | 7 | 0 | 16.0 / 22.9 | 125.37 | 1521.43 | 87.18 | -0.130 / -0.133 | -0.909 |
| entry_10_exit_5 | 4 | 0 | 88.0 / 101.3 | 163.75 | 587.96 | 22.72 | -0.101 / -0.100 | -0.304 |
| entry_15_exit_15 | tidak ada episode | - | - | - | - | - | - | - |
| entry_15_exit_7_5 | tidak ada episode | - | - | - | - | - | - | - |

### Benchmark carry selalu-hold

| Tahun/window | Status | Censored | Funding gross USDT | Fee USDT | Basis PnL USDT | Net return % |
|---|---|---:|---:|---:|---:|---:|
| all_available | censored | 1 | - | - | - | - |
| since_2023 | censored | 1 | - | - | - | - |
| 2020 | censored | 1 | - | - | - | - |
| 2021 | censored | 1 | - | - | - | - |
| 2022 | censored | 1 | - | - | - | - |
| 2023 | censored | 1 | - | - | - | - |
| 2024 | complete | 0 | 8160.53 | 206.42 | 53.09 | 9.461 |
| 2025 | complete | 0 | 5347.06 | 272.35 | 16.96 | 2.720 |
| 2026 | censored | 1 | - | - | - | - |

Benchmark yang tidak dapat dihitung karena censoring: 2020, 2021, 2022, 2023, dan 2026. Window seluruh data serta sejak 2023 juga censored.

### Output kill rule apa adanya

```json
{
  "condition_a_all_six_since_2023_total_net_return_lte_zero": false,
  "condition_b_no_combo_outperforms_complete_annual_benchmark": true,
  "comparable_benchmark_years": ["2024", "2025"],
  "benchmark_years_unavailable_due_to_censoring": ["2023", "2026"],
  "annual_outperformance_records": [],
  "kill_rule_triggered": true
}
```

`comparable_benchmark_years` berisi dua tahun, sehingga kondisi (b) dapat dievaluasi sesuai aturan yang dikunci. Tidak ada penilaian edge, CI, optimasi, atau walk-forward pada Tahap 3.

## File dan perintah

### File dipertahankan

- `data/research/funding_rate_arbitrage/stage3/ledger_entry_5_exit_5.csv`
- `data/research/funding_rate_arbitrage/stage3/ledger_entry_5_exit_2_5.csv`
- `data/research/funding_rate_arbitrage/stage3/ledger_entry_10_exit_10.csv`
- `data/research/funding_rate_arbitrage/stage3/ledger_entry_10_exit_5.csv`
- `data/research/funding_rate_arbitrage/stage3/ledger_entry_15_exit_15.csv`
- `data/research/funding_rate_arbitrage/stage3/ledger_entry_15_exit_7_5.csv`
- `data/research/funding_rate_arbitrage/stage3/stage3_benchmark_always_hold.csv`
- `data/research/funding_rate_arbitrage/stage3/stage3_summary.json`

### File diubah atau dihapus

- Diubah: `docs/FUNDING_RATE_ARBITRAGE_RESEARCH_STAGE_3.md`.
- Harness sementara yang telah dihapus setelah laporan ini: `tmp_run_stage3.py`, `tmp_stage3_ledger_engine.py`, dan `tmp_stage3_ledger_test.py`, termasuk folder `__pycache__/` yang dibuat Python.

### Perintah substantif yang dijalankan

```powershell
& C:\Users\User\miniconda3\envs\hummingbot\python.exe .\data\research\funding_rate_arbitrage\tmp_stage3_ledger_test.py
& C:\Users\User\miniconda3\envs\hummingbot\python.exe .\data\research\funding_rate_arbitrage\tmp_run_stage3.py
Remove-Item -LiteralPath data\research\funding_rate_arbitrage\tmp_run_stage3.py, data\research\funding_rate_arbitrage\tmp_stage3_ledger_engine.py, data\research\funding_rate_arbitrage\tmp_stage3_ledger_test.py
Remove-Item -LiteralPath 'D:\hummingbot\hummingbot-master\data\research\funding_rate_arbitrage\__pycache__' -Recurse -Force
```

Tes dijalankan ulang setelah setiap perbaikan yang diizinkan; pada eksekusi terakhir kelima tes lulus dan runner selesai tanpa error. Tidak ada perintah jaringan, akses API key/akun, instalasi paket, commit, atau perubahan komponen bot.

## Keputusan

- Strategi threshold funding **GAGAL** oleh kill rule kondisi (b). Tahap 4 dan Tahap 5 dilewati.
- Pada 2024, benchmark carry selalu-hold mencatat `+9,461%`, sedangkan kombinasi terbaik mencatat `+5,383%`.
- Pada 2025, benchmark mencatat `+2,720%`, sedangkan seluruh kombinasi threshold funding mencatat return modal daur ulang negatif.
- Keterbatasan: benchmark hanya comparable pada dua tahun. Satu event harga yang hilang dapat meng-censor benchmark untuk satu tahun penuh; censoring tidak acak karena episode panjang lebih mudah terkena censoring; serta simulasi tidak memodelkan likuidasi atau margin.
- Tidak ada tuning tambahan, pembangunan ulang benchmark, atau pengujian Tahap 4-5 setelah hasil ini.
