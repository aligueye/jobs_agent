import pytest
from unittest.mock import patch, MagicMock
from src.fetchers.adzuna import normalize, fetch_adzuna, _join_terms, _url


class TestNormalize:
    def test_normalize_full_record(self):
        ad = {
            "id": "12345",
            "title": "Software Engineer",
            "company": {"display_name": "Acme Corp"},
            "location": {"area": ["New York", "NY", "USA"]},
            "created": "2024-01-15T10:00:00Z",
            "redirect_url": "https://example.com/job/12345",
            "salary_min": 100000,
            "description": "Great job\nwith newlines",
        }
        result = normalize(ad)

        assert result["src_id"] == "adzuna:12345"
        assert result["title"] == "Software Engineer"
        assert result["company"] == "Acme Corp"
        assert result["location"] == "New York, NY, USA"
        assert result["created"] == "2024-01-15T10:00:00Z"
        assert result["redirect_url"] == "https://example.com/job/12345"
        assert result["salary_min"] == 100000
        assert result["description"] == "Great job with newlines"

    def test_normalize_missing_fields(self):
        ad = {"id": "999"}
        result = normalize(ad)

        assert result["src_id"] == "adzuna:999"
        assert result["title"] == ""
        assert result["company"] == ""
        assert result["location"] == ""
        assert result["description"] == ""

    def test_normalize_empty_location(self):
        ad = {"id": "1", "location": None}
        result = normalize(ad)
        assert result["location"] == ""

    def test_normalize_string_location_area(self):
        ad = {"id": "1", "location": {"area": "Single Location"}}
        result = normalize(ad)
        assert result["location"] == "Single Location"


class TestJoinTerms:
    def test_join_list(self):
        assert _join_terms(["python", "java", "go"]) == "python java go"

    def test_join_tuple(self):
        assert _join_terms(("a", "b")) == "a b"

    def test_join_set(self):
        result = _join_terms({"x"})
        assert result == "x"

    def test_join_string(self):
        assert _join_terms("already a string") == "already a string"

    def test_join_none(self):
        assert _join_terms(None) is None


class TestUrl:
    @patch("src.fetchers.adzuna.APP_ID", "test_id")
    @patch("src.fetchers.adzuna.APP_KEY", "test_key")
    def test_url_basic(self):
        query = {"where": "Boston"}
        global_params = {"results_per_page": 10, "max_days_old": 3}
        url = _url(1, query, global_params)

        assert "app_id=test_id" in url
        assert "app_key=test_key" in url
        assert "where=Boston" in url
        assert "results_per_page=10" in url
        assert "max_days_old=3" in url
        assert "/1?" in url


class TestFetchAdzuna:
    @patch("src.fetchers.adzuna.APP_ID", "test_id")
    @patch("src.fetchers.adzuna.APP_KEY", "test_key")
    @patch("src.fetchers.adzuna.requests.get")
    def test_fetch_single_page(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"id": "1", "title": "Job 1"}, {"id": "2", "title": "Job 2"}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        jobs = fetch_adzuna(
            query={"where": "NYC"},
            global_params={"pages": 1},
            sleep_s=0,
        )

        assert len(jobs) == 2
        assert jobs[0]["id"] == "1"
        mock_get.assert_called_once()

    @patch("src.fetchers.adzuna.APP_ID", "test_id")
    @patch("src.fetchers.adzuna.APP_KEY", "test_key")
    @patch("src.fetchers.adzuna.requests.get")
    def test_fetch_stops_on_empty_results(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        jobs = fetch_adzuna(
            query={"where": "NYC"},
            global_params={"pages": 5},
            sleep_s=0,
        )

        assert len(jobs) == 0
        assert mock_get.call_count == 1  # Should stop after first empty page

    @patch("src.fetchers.adzuna.APP_ID", None)
    @patch("src.fetchers.adzuna.APP_KEY", None)
    def test_fetch_missing_credentials(self):
        with pytest.raises(AssertionError, match="Missing ADZUNA creds"):
            fetch_adzuna(query={}, global_params={})
