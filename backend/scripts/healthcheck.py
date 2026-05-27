from urllib.request import urlopen


with urlopen("http://localhost:8000/", timeout=5) as response:
    raise SystemExit(0 if response.status == 200 else 1)

