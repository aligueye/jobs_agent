from jobspy import scrape_jobs
import pandas as pd


def fetch_jobspy(query: dict, global_params: dict) -> list[dict]:
    """
    Fetch jobs using JobSpy (scrapes LinkedIn, Indeed, Glassdoor, ZipRecruiter).

    Args:
        query: Dict with search_term, location, distance, site_name (optional)
        global_params: Dict with results_wanted, hours_old

    Returns:
        List of job dicts in JobSpy's raw format
    """
    site_names = query.get("site_name", ["indeed", "linkedin", "glassdoor", "zip_recruiter"])
    if isinstance(site_names, str):
        site_names = [site_names]

    search_term = query.get("search_term", "")
    if not search_term and query.get("what_or"):
        # Convert what_or list to search string for compatibility with adzuna-style config
        terms = query["what_or"]
        if isinstance(terms, list):
            search_term = " OR ".join(terms)
        else:
            search_term = terms

    location = query.get("location", query.get("where", ""))
    distance = query.get("distance", 50)
    results_wanted = global_params.get("results_wanted", global_params.get("results_per_page", 50))
    hours_old = global_params.get("hours_old", global_params.get("max_days_old", 5) * 24)

    print(f"Fetching JobSpy: '{search_term}' in '{location}' from {site_names}")

    df = scrape_jobs(
        site_name=site_names,
        search_term=search_term,
        location=location,
        distance=distance,
        results_wanted=results_wanted,
        hours_old=hours_old,
        country_indeed="USA",
    )

    # Convert DataFrame to list of dicts
    jobs = df.to_dict(orient="records") if not df.empty else []
    print(f"Found {len(jobs)} jobs from JobSpy")
    return jobs


def normalize(job: dict) -> dict:
    """
    Normalize a JobSpy job record to match the standard schema.
    """
    # Handle NaN values from pandas
    def clean(val):
        if pd.isna(val):
            return None
        return val

    job_url = clean(job.get("job_url", ""))
    site = clean(job.get("site", "jobspy"))
    job_id = clean(job.get("id", "")) or job_url

    return {
        "src_id": f"{site}:{job_id}",
        "title": clean(job.get("title", "")),
        "company": clean(job.get("company", "")),
        "location": clean(job.get("location", "")),
        "created": clean(job.get("date_posted", "")),
        "redirect_url": job_url,
        "salary_min": clean(job.get("min_amount")),
        "salary_max": clean(job.get("max_amount")),
        "description": (clean(job.get("description", "")) or "").replace("\n", " ").strip(),
    }
