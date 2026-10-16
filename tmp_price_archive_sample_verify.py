from __future__ import annotations

import hashlib
import io
import zipfile

import requests


SAMPLES = {
    "spot": "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2020-01.zip",
    "futures": "https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2020-01.zip",
    "mark": "https://data.binance.vision/data/futures/um/monthly/markPriceKlines/BTCUSDT/1m/BTCUSDT-1m-2020-01.zip",
}

for name, url in SAMPLES.items():
    content = requests.get(url, timeout=90).content
    checksum = requests.get(url + ".CHECKSUM", timeout=30).text.split()[0]
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        member = archive.namelist()[0]
        first_line = archive.read(member).decode("utf-8").splitlines()[0]
    print(name, "sha256_match=", hashlib.sha256(content).hexdigest() == checksum, "member=", member, "first=", first_line)
