import csv, json, yaml
from pathlib import Path

from src.fetchers.adzuna import fetch_adzuna, normalize as normalize_adzuna
from src.fetchers.jobspy import fetch_jobspy, normalize as normalize_jobspy

ROOT = Path(__file__).resolve().parents[1]
cfg = yaml.safe_load(open(ROOT / "configs/sources.yaml"))


def main():
    out_jsonl = ROOT / "data/jobs_raw.jsonl"
    out_csv = ROOT / "data/jobs.csv"
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)

    all_jobs = []
    global_params = cfg.get("global_params", {})

    for q in cfg["queries"]:
        source = q.get("source", "adzuna")

        if source == "adzuna":
            jobs = fetch_adzuna(query=q, global_params=global_params)
            normalized = [normalize_adzuna(j) for j in jobs]
        elif source == "jobspy":
            jobs = fetch_jobspy(query=q, global_params=global_params)
            normalized = [normalize_jobspy(j) for j in jobs]
        else:
            print(f"Unknown source: {source}, skipping")
            continue

        all_jobs.extend([(j, n) for j, n in zip(jobs, normalized)])

    # write raw
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for raw, _ in all_jobs:
            f.write(json.dumps(raw, ensure_ascii=False, default=str) + "\n")

    # normalized CSV
    rows = [n for _, n in all_jobs]
    cols = [
        "src_id",
        "title",
        "company",
        "location",
        "created",
        "salary_min",
        "salary_max",
        "redirect_url",
        "description",
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in cols})

    print(f"Wrote {out_csv} ({len(rows)} rows) and {out_jsonl}")


if __name__ == "__main__":
    main()
