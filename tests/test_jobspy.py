import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from src.fetchers.jobspy import normalize, fetch_jobspy


class TestNormalize:
    def test_normalize_full_record(self):
        job = {
            "id": "abc123",
            "site": "linkedin",
            "title": "Backend Developer",
            "company": "Tech Inc",
            "location": "San Francisco, CA",
            "date_posted": "2024-01-20",
            "job_url": "https://linkedin.com/jobs/abc123",
            "min_amount": 120000,
            "max_amount": 180000,
            "description": "Join our team\nand build great things",
        }
        result = normalize(job)

        assert result["src_id"] == "linkedin:abc123"
        assert result["title"] == "Backend Developer"
        assert result["company"] == "Tech Inc"
        assert result["location"] == "San Francisco, CA"
        assert result["created"] == "2024-01-20"
        assert result["redirect_url"] == "https://linkedin.com/jobs/abc123"
        assert result["salary_min"] == 120000
        assert result["salary_max"] == 180000
        assert result["description"] == "Join our team and build great things"

    def test_normalize_with_nan_values(self):
        job = {
            "id": np.nan,
            "site": "indeed",
            "title": "Engineer",
            "company": np.nan,
            "location": "Remote",
            "date_posted": np.nan,
            "job_url": "https://indeed.com/job/xyz",
            "min_amount": np.nan,
            "max_amount": np.nan,
            "description": "A job",
        }
        result = normalize(job)

        assert result["src_id"] == "indeed:https://indeed.com/job/xyz"
        assert result["company"] is None
        assert result["created"] is None
        assert result["salary_min"] is None
        assert result["salary_max"] is None

    def test_normalize_missing_fields(self):
        job = {"job_url": "https://example.com/job"}
        result = normalize(job)

        assert "jobspy" in result["src_id"]
        # Missing fields return None after clean() processes them
        assert result["title"] is None or result["title"] == ""
        assert result["company"] is None or result["company"] == ""

    def test_normalize_uses_url_as_fallback_id(self):
        job = {"job_url": "https://glassdoor.com/job/999", "site": "glassdoor"}
        result = normalize(job)
        assert result["src_id"] == "glassdoor:https://glassdoor.com/job/999"


class TestFetchJobspy:
    @patch("src.fetchers.jobspy.scrape_jobs")
    def test_fetch_returns_jobs(self, mock_scrape):
        mock_df = pd.DataFrame([
            {"id": "1", "title": "Job 1", "site": "indeed"},
            {"id": "2", "title": "Job 2", "site": "linkedin"},
        ])
        mock_scrape.return_value = mock_df

        jobs = fetch_jobspy(
            query={"search_term": "python developer", "location": "NYC"},
            global_params={"results_wanted": 10},
        )

        assert len(jobs) == 2
        assert jobs[0]["title"] == "Job 1"
        mock_scrape.assert_called_once()

    @patch("src.fetchers.jobspy.scrape_jobs")
    def test_fetch_empty_results(self, mock_scrape):
        mock_scrape.return_value = pd.DataFrame()

        jobs = fetch_jobspy(
            query={"search_term": "nonexistent job"},
            global_params={},
        )

        assert len(jobs) == 0

    @patch("src.fetchers.jobspy.scrape_jobs")
    def test_fetch_uses_what_or_as_search_term(self, mock_scrape):
        mock_scrape.return_value = pd.DataFrame()

        fetch_jobspy(
            query={"what_or": ["python", "java", "go"]},
            global_params={},
        )

        call_kwargs = mock_scrape.call_args[1]
        assert "python OR java OR go" in call_kwargs["search_term"]

    @patch("src.fetchers.jobspy.scrape_jobs")
    def test_fetch_uses_where_as_location(self, mock_scrape):
        mock_scrape.return_value = pd.DataFrame()

        fetch_jobspy(
            query={"where": "Boston, MA"},
            global_params={},
        )

        call_kwargs = mock_scrape.call_args[1]
        assert call_kwargs["location"] == "Boston, MA"

    @patch("src.fetchers.jobspy.scrape_jobs")
    def test_fetch_site_name_string_converted_to_list(self, mock_scrape):
        mock_scrape.return_value = pd.DataFrame()

        fetch_jobspy(
            query={"search_term": "dev", "site_name": "indeed"},
            global_params={},
        )

        call_kwargs = mock_scrape.call_args[1]
        assert call_kwargs["site_name"] == ["indeed"]

    @patch("src.fetchers.jobspy.scrape_jobs")
    def test_fetch_converts_max_days_old_to_hours(self, mock_scrape):
        mock_scrape.return_value = pd.DataFrame()

        fetch_jobspy(
            query={"search_term": "dev"},
            global_params={"max_days_old": 7},
        )

        call_kwargs = mock_scrape.call_args[1]
        assert call_kwargs["hours_old"] == 168  # 7 * 24
