import time, json
from pathlib import Path
from src.tools.fetch_url import fetch_url

CACHE = Path("data/fetch_cache")
CACHE.mkdir(parents=True, exist_ok=True)


def _cache_path(url: str) -> Path:
    import hashlib

    return CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".json")


def fetch_and_cache(url: str) -> str:
    """Fetch a page once and reuse cached text later."""
    path = _cache_path(url)
    if path.exists():
        return json.loads(path.read_text()).get("text", "")
    text = fetch_url(url)
    path.write_text(json.dumps({"text": text}, ensure_ascii=False))
    time.sleep(0.3)  # polite pause
    return text
