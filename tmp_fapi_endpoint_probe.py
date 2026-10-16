import requests


HOSTS = [
    "fapi.binance.com",
    "fapi1.binance.com",
    "fapi2.binance.com",
    "fapi3.binance.com",
    "fapi4.binance.com",
]
PATH = "/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1568073600000&limit=1"

for host in HOSTS:
    try:
        response = requests.get(f"https://{host}{PATH}", timeout=12)
        print(host, response.status_code, response.text[:120])
    except Exception as exc:
        print(host, type(exc).__name__, str(exc).split("\n")[0][:180])
