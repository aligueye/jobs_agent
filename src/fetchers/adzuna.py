import os, time, requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

BASE = "https://api.adzuna.com/v1/api/jobs/us/search"


def _join_terms(v):
    if v is None:
        return None
    if isinstance(v, (list, tuple, set)):
        return " ".join(map(str, v))
    return str(v)


def _url(page: int, query: dict, global_params: dict) -> str:
    q = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": _join_terms(query.get("what", "")),
        "what_or": _join_terms(query.get("what_or", None)),
        "what_exclude": _join_terms(query.get("what_exclude", None)),
        "where": query.get("where", ""),
        "distance": query.get("distance_km", query.get("distance", 50)),  # km
        "results_per_page": global_params.get("results_per_page", 50),
        "max_days_old": global_params.get("max_days_old", 5),
        "salary_min": global_params.get("salary_min"),
    }
    q = {k: v for k, v in q.items() if v not in (None, "", [])}
    return f"{BASE}/{page}?{urlencode(q)}"


def fetch_adzuna(query: dict, global_params: dict, sleep_s: float = 0.2):
    assert APP_ID and APP_KEY, "Missing ADZUNA creds in .env"
    jobs, pages = [], global_params.get("pages", 1)
    for p in range(1, pages + 1):
        url = _url(p, query, global_params)
        print(f"Fetching Adzuna page {p}: {url} \n")
        r = requests.get(url, timeout=20)  # no content-type in query
        try:
            r.raise_for_status()
        except requests.HTTPError:
            print("URL:", r.url)
            print("Body:", r.text[:1000])
            raise
        payload = r.json()
        results = payload.get("results", [])
        jobs.extend(results)
        if not results:
            break
        time.sleep(sleep_s)
    return jobs


def normalize(ad):
    loc = ad.get("location") or {}
    area = loc.get("area") or []
    return {
        "src_id": f"adzuna:{ad.get('id')}",
        "title": ad.get("title", ""),
        "company": (ad.get("company") or {}).get("display_name", ""),
        "location": ", ".join(area) if isinstance(area, list) else str(area),
        "created": ad.get("created", ""),
        "url": ad.get("redirect_url", ""),
        "salary_min": ad.get("salary_min"),
        "description": (ad.get("description") or "").replace("\n", " ").strip(),
    }
