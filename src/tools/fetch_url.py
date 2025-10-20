import requests, bs4, re


def fetch_url(url: str) -> str:
    """
    Fetches any URL and returns cleaned text content (max ~8k chars).
    Designed for LangChain tool use.
    """
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "jobs-agent/0.1 (+local)"},
            timeout=8,
            allow_redirects=True,
        )
        if r.status_code != 200:
            return f"[error: http {r.status_code}]"
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        for t in soup(["script", "style", "nav", "footer", "header"]):
            t.decompose()
        text = " ".join(x.get_text(" ", strip=True) for x in soup.select("h1,h2,p,li"))
        text = re.sub(r"\s+", " ", text)
        return text[:8000]  # truncate to stay LLM-friendly
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return f"[error: {e}]"
