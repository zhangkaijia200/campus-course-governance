import json
import urllib.request

payload = json.dumps({"username": "student1", "password": "demo123"}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8000/auth/login",
    data=payload,
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=5) as resp:
    print(json.loads(resp.read())["access_token"])
