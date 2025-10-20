import csv, json, os, yaml
from pathlib import Path
from src.fetchers.adzuna import fetch_adzuna, normalize

ROOT = Path(__file__).resolve().parents[1]
cfg = yaml.safe_load(open(ROOT / "configs/sources.yaml"))


def main():
    out_jsonl = ROOT / "data/jobs_raw.jsonl"
    out_csv = ROOT / "data/jobs.csv"
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)

    all_jobs = []
    for q in cfg["queries"]:
        ads = fetch_adzuna(query=q, global_params=cfg.get("global_params", {}))
        all_jobs.extend(ads)

    # write raw
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for ad in all_jobs:
            f.write(json.dumps(ad, ensure_ascii=False) + "\n")

    # normalize + CSV
    rows = [normalize(a) for a in all_jobs]
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
