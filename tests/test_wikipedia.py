from unittest.mock import patch, MagicMock
import wikipedia as wiki_lib
from agent.tools.wikipedia import run as wiki_run


def test_search_returns_summary():
    fake_page = MagicMock()
    fake_page.title = "Alan Turing"
    fake_page.summary = "Alan Mathison Turing was an English mathematician..."
    fake_page.url = "https://en.wikipedia.org/wiki/Alan_Turing"
    with patch("agent.tools.wikipedia.wikipedia.page", return_value=fake_page):
        with patch("agent.tools.wikipedia.wikipedia.search", return_value=["Alan Turing"]):
            result = wiki_run({"op": "search", "query": "Alan Turing"})
    assert result["ok"] is True
    assert "Turing" in result["result"]["summary"]
    assert result["result"]["title"] == "Alan Turing"


def test_disambiguation_returns_options():
    err = wiki_lib.exceptions.DisambiguationError("Mercury", ["Mercury (planet)", "Mercury (element)", "Freddie Mercury"])
    with patch("agent.tools.wikipedia.wikipedia.search", return_value=["Mercury"]):
        with patch("agent.tools.wikipedia.wikipedia.page", side_effect=err):
            result = wiki_run({"op": "search", "query": "Mercury"})
    assert result["ok"] is False
    assert result["error_type"] == "disambiguation"


def test_page_not_found():
    err = wiki_lib.exceptions.PageError(pageid="xyznotreal")
    with patch("agent.tools.wikipedia.wikipedia.search", return_value=[]):
        with patch("agent.tools.wikipedia.wikipedia.page", side_effect=err):
            result = wiki_run({"op": "search", "query": "xyznotreal"})
    assert result["ok"] is False
    assert result["error_type"] == "not_found"


def test_extract_returns_full_content_slice():
    fake_page = MagicMock()
    fake_page.title = "NVIDIA"
    fake_page.content = "NVIDIA Corporation is an American multinational tech company. " * 100
    fake_page.url = "https://en.wikipedia.org/wiki/NVIDIA"
    with patch("agent.tools.wikipedia.wikipedia.page", return_value=fake_page):
        result = wiki_run({"op": "extract", "page": "NVIDIA"})
    assert result["ok"] is True
    assert "NVIDIA" in result["result"]["content"]
    assert len(result["result"]["content"]) <= 4000
