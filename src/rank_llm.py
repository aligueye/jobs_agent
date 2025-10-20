import csv, json
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.memory import get_retriever
from src.enrich import fetch_and_cache


RANK_SCHEMA = {
    "id": "<int | null> (local DB id if present)",
    "external_id": "<string> (unique key like 'adzuna:123456')",
    "description": "<string> (job description text)",
    "redirect_url": "<string> (job posting URL)",
    "company": "<string> (company name)",
    "title": "<string> (job title)",
    "location": "<string> (job location)",
    "score": "<int 0-100, higher = better fit>",
    "why": "<short summary <=280 chars>",
    "level_fit": "<one of: junior | mid | senior | staff | unknown>",
    "tech_fit": ["<relevant tech keywords>"],
    "location_fit": "<perfect | ok | poor>",
    "relevance_tags": ["<keywords like fintech, backend, ai>"],
    "summary": "<1-2 sentence human-readable job synopsis>",
    "concerns": ["<potential issues or mismatches>"],
}

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert technical career assistant. "
            "Compare the candidate’s profile and the job posting, "
            "then return STRICT JSON following {schema}. "
            "Be concise, factual, and do not include extra text.",
        ),
        ("user", "PROFILE FACTS:\n{facts}\n\n" "JOB DATA:\n{job}"),
    ]
).partial(schema=json.dumps(RANK_SCHEMA, indent=2))

TOP_K = 20


def rank_jobs(
    jobs_csv="data/jobs.csv",
    out_path="data/jobs_ranked.csv",
    top_k_path="data/jobs_top_k.csv",
):
    retriever = get_retriever()
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    rows = list(csv.DictReader(open(jobs_csv, encoding="utf-8")))
    scored = []
    for r in rows:
        query = f"Key skills/exp relevant to: {r['title']} at {r['company']} in {r['location']}"
        docs = retriever.invoke(query)

        facts = "\n".join(d.page_content for d in docs) if docs else ""
        job_json = json.dumps(
            {
                "id": r.get("id", None),
                "external_id": r.get("src_id", None),
                "title": r.get("title", ""),
                "company": r.get("company", ""),
                "location": r.get("location", ""),
                "description": r.get("description", ""),
                "redirect_url": r.get("redirect_url", ""),
            }
        )
        msg = PROMPT.format_messages(facts=facts, job=job_json)
        resp = llm.invoke(msg).content.strip()
        try:
            data = json.loads(resp)
            data["id"] = r.get("id", None)
            data["external_id"] = r.get("src_id", None)
            scored.append(data)
            print(f"Ranked job {data['external_id']} with score {data['score']}!")
        except Exception as e:
            print(f"Error parsing LLM response for job {r.get('src_id', '')}: {e}")
            print("Response was:", resp)

    scored.sort(key=lambda x: float(x["score"]), reverse=True)
    cols = RANK_SCHEMA.keys()
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for s in scored:
            w.writerow({k: s.get(k, "") for k in cols})
    print(f"Wrote {out_path} ({len(scored)} rows) \n")

    # Further investigation of top K jobs
    for r in scored[:TOP_K]:
        full_text = fetch_and_cache(r.get("redirect_url", ""))
        if full_text and not full_text.startswith("[error"):
            r["description_enriched"] = full_text
    print(scored)
    # Rerank top K with enriched descriptions
    for r in scored[:TOP_K]:
        query = f"Key skills/exp relevant to: {r['title']} at {r['company']} in {r['location']}"
        docs = retriever.invoke(query)
        facts = "\n".join(d.page_content for d in docs) if docs else ""
        job_json = json.dumps(
            {
                "id": r.get("id", None),
                "external_id": r.get("external_id", None),
                "title": r.get("title", ""),
                "company": r.get("company", ""),
                "location": r.get("location", ""),
                "description": r.get("description_enriched", r.get("description", "")),
                "redirect_url": r.get("redirect_url", ""),
            }
        )
        msg = PROMPT.format_messages(facts=facts, job=job_json)
        resp = llm.invoke(msg).content.strip()
        try:
            data = json.loads(resp)
            data["id"] = r.get("id", None)
            data["external_id"] = r.get("external_id", None)
            print(
                f"Re-ranked enriched job {data['external_id']} with score {data['score']}!"
            )
            for k in data:
                r[k] = data[k]
        except Exception as e:
            print(
                f"Error parsing LLM response for enriched job {r.get('external_id', '')}: {e}"
            )
            print("Response was:", resp)

    scored.sort(key=lambda x: float(x["score"]), reverse=True)
    with open(top_k_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for s in scored:
            w.writerow({k: s.get(k, "") for k in cols})
    print(f"Wrote {top_k_path} ({len(scored)} rows) \n")


if __name__ == "__main__":
    rank_jobs()
