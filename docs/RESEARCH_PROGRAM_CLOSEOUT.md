# Penutupan Program Riset BTCUSDT

## Status

Dokumen ini menutup lima hipotesis offline yang telah diuji. Bot demo/paper tetap tidak diubah. Tidak ada strategi pada tabel ini yang diteruskan ke penerapan produksi oleh dokumen penutupan ini.

## Ringkasan hipotesis

| Hipotesis | Status | Jumlah trade/episode | Expectancy net | CI | Penyebab utama |
|---|---|---:|---|---|---|
| Continuation 5m | Gagal walk-forward | 763 trade; win rate kotor 46,92%; TP 62 / SL 166 / time 535 | Grid terbaik 2023+: -0,303% pada TP 0,5% / SL 1,5% | Grid: [-0,377%; -0,229%]. Test 2026: -0,402%, CI [-0,573%; -0,231%] | Gagal walk-forward. |
| Mean-reversion 5m | Gagal in-sample | Sekitar 4.140-4.274 trade per kombinasi; 6 kombinasi | -0,291% s.d. -0,294% | CI atas < 0 untuk seluruh kombinasi | Early-stop. |
| Continuation 4 jam | Inconclusive | 9 kandidat sejak 2023 | Tidak tersedia | Tidak tersedia | Sampel tidak memadai untuk grid search dan walk-forward. |
| Mean-reversion 4 jam | Inconclusive, train negatif | Sekitar 50-52 trade per kombinasi; 6 kombinasi. Walk-forward: train n=40, test n=10 | Terbaik 2,0 ATR / 24 candle: -0,101%. Train: -0,167%. Test: +0,166% | Kombinasi terbaik: [-0,757%; +0,555%]. Test: [-1,327%; +1,659%] | Train negatif dan sampel test tipis. |
| Funding threshold | Gagal kill rule Tahap 3 | 6 kombinasi | Tidak tersedia. Return modal daur ulang sejak 2023: -15,158% s.d. +6,309% | Tidak tersedia | Kill rule kondisi (b) terpicu. |

## Pelajaran metodologis

1. Biaya realistis harus dihitung sejak evaluasi awal, bukan setelah strategi terlihat menarik secara kotor.
2. Aturan entry, exit, biaya, dan kill rule perlu dikunci sebelum data hasil dibaca.
3. Hasil gagal, hasil inconclusive, dan hasil lolos harus dipisahkan; sampel kecil tidak boleh diperlakukan sebagai bukti keberhasilan.
4. Confidence interval dan walk-forward diperlukan untuk membedakan hasil rata-rata dari variasi sampel.
5. Data censored perlu dipertahankan dan dilaporkan, bukan diganti dengan exit sintetis atau dihapus diam-diam.
6. Benchmark harus memakai horizon dan definisi return yang sebanding dengan strategi yang diuji.
7. Tuning setelah hasil diketahui mengubah pengujian menjadi optimasi pasca-hasil dan tidak boleh dipakai sebagai bukti baru.
8. Riset offline harus tetap terisolasi dari bot, controller, konfigurasi, serta akun trading sampai seluruh gerbang validasi terpenuhi.

## Syarat hipotesis baru

Hipotesis baru hanya dapat memasuki program riset bila seluruh syarat berikut dikunci sebelum data dianalisis:

1. Kill rule ditulis dan dikunci sebelum data hasil dibaca.
2. Biaya realistis dua sisi dimasukkan ke simulasi.
3. Dataset dipisahkan berdasarkan waktu menjadi bagian pengembangan dan bagian uji.
4. Parameter yang dipilih menjalani walk-forward tanpa perubahan pada test set.
5. Forward paper test pada data baru menjadi gerbang terakhir sebelum ada pembahasan penerapan.
6. Tidak ada tuning setelah melihat hasil, termasuk penambahan filter, perubahan benchmark, atau redefinisi exit untuk memperbaiki hasil yang telah gagal.

## Batas penutupan

- Tahap 4 dan Tahap 5 funding arbitrage tidak dijalankan.
- Ledger dan ringkasan `data/research/funding_rate_arbitrage/stage3/` tidak diubah.
- Bot, controller, konfigurasi, API key, dan akun trading tidak disentuh.
