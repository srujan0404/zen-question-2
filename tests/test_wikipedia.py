from unittest.mock import patch, MagicMock
from agent.tools.wikipedia import run as wiki_run


def _fake_response(status_code=200, json_data=None, raise_for_status=False):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}
    if raise_for_status:
        from requests import HTTPError
        resp.raise_for_status.side_effect = HTTPError(response=resp)
    else:
        resp.raise_for_status.return_value = None
    return resp


def test_search_returns_summary():
    summary_payload = {
        "title": "Alan Turing",
        "extract": "Alan Mathison Turing was an English mathematician...",
        "description": "English mathematician (1912-1954)",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Alan_Turing"}},
        "type": "standard",
    }
    with patch("agent.tools.wikipedia.requests.get", return_value=_fake_response(200, summary_payload)):
        result = wiki_run({"op": "search", "query": "Alan Turing"})
    assert result["ok"] is True
    assert "Turing" in result["result"]["summary"]
    assert result["result"]["title"] == "Alan Turing"
    assert "Alan_Turing" in result["result"]["url"]


def test_search_disambiguation_returns_options():
    summary_payload = {"title": "Mercury", "type": "disambiguation", "extract": ""}
    opensearch_payload = ["Mercury", ["Mercury (planet)", "Mercury (element)", "Freddie Mercury"], [], []]

    def fake_get(url, *args, **kwargs):
        if "rest_v1" in url:
            return _fake_response(200, summary_payload)
        return _fake_response(200, opensearch_payload)

    with patch("agent.tools.wikipedia.requests.get", side_effect=fake_get):
        result = wiki_run({"op": "search", "query": "Mercury"})
    assert result["ok"] is False
    assert result["error_type"] == "disambiguation"
    assert "Mercury (planet)" in result["error"]


def test_search_page_not_found():
    not_found_resp = _fake_response(404, {})
    opensearch_empty = ["xyznotreal", [], [], []]

    def fake_get(url, *args, **kwargs):
        if "rest_v1" in url:
            return not_found_resp
        return _fake_response(200, opensearch_empty)

    with patch("agent.tools.wikipedia.requests.get", side_effect=fake_get):
        result = wiki_run({"op": "search", "query": "xyznotreal"})
    assert result["ok"] is False
    assert result["error_type"] == "not_found"


def test_extract_returns_content_slice():
    extract_payload = {
        "query": {
            "pages": {
                "12345": {
                    "title": "NVIDIA",
                    "extract": "NVIDIA Corporation is an American multinational tech company. " * 100,
                    "fullurl": "https://en.wikipedia.org/wiki/NVIDIA",
                }
            }
        }
    }
    with patch("agent.tools.wikipedia.requests.get", return_value=_fake_response(200, extract_payload)):
        result = wiki_run({"op": "extract", "page": "NVIDIA"})
    assert result["ok"] is True
    assert "NVIDIA" in result["result"]["content"]
    assert len(result["result"]["content"]) <= 4000
    assert result["result"]["truncated"] is True


def test_missing_query_returns_bad_input():
    result = wiki_run({"op": "search"})
    assert result["ok"] is False
    assert result["error_type"] == "bad_input"
