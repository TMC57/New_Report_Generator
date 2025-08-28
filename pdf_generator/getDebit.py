import os, requests, time, json, base64
import random, time

BASE = "https://sh1.cm2w.net"
LOGIN_URL  = f"{BASE}/cm2w-api/v2/users/login"
EVENTS_URL = f"{BASE}/cm2w-api/v2/events"

EMAIL = "e-service@tmh-corporation.com"
PASSWORD = "Jer160276@"
TDFP = os.environ.get("CM2W_TDFP")  # si requis par l'API

def login_session_cm2w():
    s = requests.Session()
    s.headers.update({
        "Accept": "application/json",
        "Content-Type": "application/json",
        # Si nécessaire (WAF) :
        # "Origin": "https://app.cm2w.net",
        # "Referer": "https://app.cm2w.net/",
        # "User-Agent": "Mozilla/5.0",
    })
    payload = {"email": EMAIL, "password": PASSWORD}
    if TDFP:
        payload["tdfp"] = TDFP
    r = s.post(LOGIN_URL, json=payload, timeout=30)
    r.raise_for_status()

    token = None
    try:
        data = r.json()
        token = data.get("token") or data.get("accessToken") or data.get("jwt")
    except Exception:
        pass
    if token:
        s.headers["Authorization"] = f"Bearer {token}"

    if "JSESSIONID" not in s.cookies and not token:
        raise RuntimeError("Pas de JSESSIONID ni de token après login.")
    return s, token

def get_events(session, device_id, from_ms, thru_ms, page=1, size=5000):
    params = {
        "deviceId": str(device_id),
        "reportType": "flowrate",
        "fromDate": str(from_ms),
        "thruDate": str(thru_ms),
        "pageNumber": str(page),
        "pageSize": str(size),
        "endPoint": "events",
    }

    time.sleep(1.5 + random.random() * 1.5)  # entre 1.5s et 3s

    resp = session.get(EVENTS_URL, params=params, timeout=60)
    if resp.status_code == 401:
        raise PermissionError("401 sur /events : token/cookie invalide ou expiré.")
    resp.raise_for_status()
    return resp.json()

# --- Utilisation ---
# 1) On s'authentifie UNE fois
# session, token = login_session_cm2w()

# 2) Plus tard, on réutilise LA MÊME session
# events = get_events(session, device_id=56753, from_ms=1751320800000, thru_ms=1753912800000)
# print("events:", type(events), len(events) if isinstance(events, list) else "json")
