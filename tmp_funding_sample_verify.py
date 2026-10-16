from __future__ import annotations

import hashlib
import io
import zipfile

import requests


BASE = "https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/"
NAME = "BTCUSDT-fundingRate-2020-01.zip"

archive_response = requests.get(BASE + NAME, timeout=60)
archive_response.raise_for_status()
checksum_response = requests.get(BASE + NAME + ".CHECKSUM", timeout=30)
checksum_response.raise_for_status()

actual_hash = hashlib.sha256(archive_response.content).hexdigest()
expected_hash = checksum_response.text.split()[0]
with zipfile.ZipFile(io.BytesIO(archive_response.content)) as archive:
    file_name = archive.namelist()[0]
    rows = archive.read(file_name).decode("utf-8").splitlines()

print("sha256_match=", actual_hash == expected_hash)
print("file=", file_name)
print("rows=", len(rows))
print("first=", rows[0])
print("last=", rows[-1])
