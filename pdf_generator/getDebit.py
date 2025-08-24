import os, requests
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

BASE = "https://sh1.cm2w.net/"
LOGIN_URL  = f"{BASE}/cm2w-api/v2/users/login/"
EVENTS_URL = f"{BASE}/cm2w-api/v2/events"

EMAIL = "e-service@tmh-corporation.com"
PASSWORD = "Jer160276@"
TDFP = os.environ.get("CM2W_TDFP")  # facultatif si l'API l'exige

def paris_ms(y, m, d, hh=0, mm=0, ss=0):
    dt = datetime(y, m, d, hh, mm, ss)
    return int(dt.timestamp() * 1000)

with requests.Session() as s:
    s.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        # Optionnel si le serveur le demande :
        # "Origin": "https://app.cm2w.net/",
        # "Referer": "https://app.cm2w.net/",
    })
    payload = {"email": EMAIL, "password": PASSWORD}
    if TDFP:
        payload["tdfp"] = TDFP

    r = s.post(LOGIN_URL, json=payload, timeout=30)
    r.raise_for_status()

    # 1) Cookie de session ?
    got_cookie = "JSESSIONID" in s.cookies

    # 2) Token dans la réponse ?
    token = None
    try:
        data = r.json()
        token = data.get("token") or data.get("accessToken") or data.get("jwt")
    except Exception:
        pass
    if token:
        s.headers["Authorization"] = f"Bearer {token}"

    if not got_cookie and not token:
        raise RuntimeError("Aucun JSESSIONID ni token après login. Vérifie l’endpoint et la charge utile.")

    params = {
        "deviceId": "56753",
        "reportType": "flowrate",
        "fromDate": 1748728800000,
        "thruDate": 1751234400000,
        "pageNumber": "1",
        "pageSize": "5000",  # pagine plutôt que 2^31-1
        "endPoint": "events",
    }
    resp = s.get(EVENTS_URL, params=params, timeout=60)
    resp.raise_for_status()
    events = resp.json()
    print("OK, événements récupérés :", (len(events) if isinstance(events, list) else "objet JSON"))