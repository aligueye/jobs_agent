import os, time, requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

APP_ID  = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

BASE = f"https://api.adzuna.com/v1/api/jobs/us/search"


def _url(page:int, params:dict)->str:
    q = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": params.get("results_per_page", 50),
        "what": params["what"],
        "where": params.get("where",""),
        "max_days_old": params.get("max_days_old", 5),
        "content-type": "application/json"
    }
    return f"{BASE}/{page}?{urlencode(q)}"

def fetch_adzuna(what:str, where:str="", pages:int=1, rpp:int=50, sleep_s:float=0.2):
    assert APP_ID and APP_KEY, "Missing ADZUNA creds in .env"
    jobs = []
    for p in range(1, pages+1):
        url = _url(p, {"what": what, "where": where, "results_per_page": rpp})
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        payload = r.json()
        jobs.extend(payload.get("results", []))
        time.sleep(sleep_s)
        if not payload.get("results"): break
    return jobs

def normalize(ad):
    # Adzuna fields: id, title, location, created, redirect_url, company, description
    loc = ad.get("location", {}) or {}
    area = loc.get("area") or []
    return {
        "src_id": f"adzuna:{ad.get('id')}",
        "title": ad.get("title",""),
        "company": (ad.get("company") or {}).get("display_name",""),
        "location": ", ".join(area) if isinstance(area, list) else str(area),
        "created": ad.get("created",""),
        "url": ad.get("redirect_url",""),
        "salary_min": ad.get("salary_min"),
        "salary_max": ad.get("salary_max"),
        "desc": (ad.get("description") or "").replace("\n"," ").strip(),
    }