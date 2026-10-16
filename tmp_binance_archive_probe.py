import requests
import pandas as pd


months = pd.date_range("2019-09-01", "2021-01-01", freq="MS")
for month in months:
    label = month.strftime("%Y-%m")
    url = f"https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-{label}.zip"
    try:
        response = requests.head(url, timeout=20, allow_redirects=True)
        print(label, response.status_code, response.headers.get("Content-Length"))
    except Exception as exc:
        print(label, type(exc).__name__, str(exc).split("\n")[0])
