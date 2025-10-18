import csv, json
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.memory import get_retriever

PROMPT = ChatPromptTemplate.from_messages([
  ("system", "You score job postings for this candidate from 0-100 and explain briefly. "
             "Use retrieved profile facts; be strict on level/stack/location. Output JSON lines."),
  ("user", "PROFILE FACTS:\n{facts}\n\nJOB:\n{job}")
])

def rank_jobs(jobs_csv="data/jobs.csv", out_path="data/jobs_ranked.csv"):
    retriever = get_retriever()
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    rows = list(csv.DictReader(open(jobs_csv, encoding="utf-8")))
    scored = []
    for r in rows:
        query = f"Key skills/exp relevant to: {r['title']} at {r['company']} in {r['location']}"
        docs = retriever.invoke(query)
        facts = "\n".join(d.page_content for d in docs) if docs else ""
        job_json = json.dumps({"title": r["title"], "company": r["company"],
                               "location": r["location"], "desc": "", "url": r["url"]})
        msg = PROMPT.format_messages(facts=facts, job=job_json)
        resp = llm.invoke(msg).content.strip()
        # expect JSON like: {"score": 78, "why": "…"}
        try:
            data = json.loads(resp)
            r["score"], r["why"] = data.get("score", 0), data.get("why","")
        except Exception:
            r["score"], r["why"] = 0, resp[:200]
        scored.append(r)

    scored.sort(key=lambda x: float(x["score"]), reverse=True)
    cols = ["score","title","company","location","url","why"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for s in scored: w.writerow({k: s.get(k, "") for k in cols})
    print(f"Wrote {out_path} ({len(scored)} rows)")

if __name__ == "__main__":
    rank_jobs()