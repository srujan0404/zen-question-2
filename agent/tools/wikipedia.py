import requests

MAX_CONTENT_CHARS = 4000
USER_AGENT = "ZenQ2Agent/1.0 (educational submission; contact: dharmassr@example.com)"
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}
TIMEOUT = 10


def _search_titles(query: str) -> list[str]:
    """Use opensearch to find candidate page titles for a query."""
    r = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "opensearch",
            "search": query,
            "limit": 5,
            "namespace": 0,
            "format": "json",
        },
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    return data[1] if len(data) > 1 else []


def _get_summary(title: str) -> dict:
    """REST API summary endpoint — returns extract, description, url, and disambiguation hint."""
    safe_title = requests.utils.quote(title.replace(" ", "_"), safe="")
    r = requests.get(
        f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe_title}",
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    if r.status_code == 404:
        return {"_not_found": True, "title": title}
    r.raise_for_status()
    return r.json()


def _get_extract(title: str) -> dict:
    """Action API plain-text extract for fuller content."""
    r = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "prop": "extracts|info",
            "explaintext": 1,
            "redirects": 1,
            "inprop": "url",
            "titles": title,
            "format": "json",
        },
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    if not pages:
        return {"_not_found": True, "title": title}
    page = next(iter(pages.values()))
    if "missing" in page:
        return {"_not_found": True, "title": title}
    return {
        "title": page.get("title", title),
        "extract": page.get("extract", ""),
        "url": page.get("fullurl", f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"),
    }


def run(args: dict) -> dict:
    op = args.get("op", "search")
    query = args.get("query") or args.get("page")
    if not query or not isinstance(query, str):
        return {"ok": False, "error": "missing or non-string 'query'", "error_type": "bad_input"}

    try:
        if op == "search":
            summary = _get_summary(query)
            if summary.get("_not_found"):
                candidates = _search_titles(query)
                if not candidates:
                    return {
                        "ok": False,
                        "error": f"no Wikipedia page found for '{query}'",
                        "error_type": "not_found",
                    }
                summary = _get_summary(candidates[0])
                if summary.get("_not_found"):
                    return {
                        "ok": False,
                        "error": f"could not retrieve page for '{query}'. Candidates: {candidates}",
                        "error_type": "not_found",
                    }
            if summary.get("type") == "disambiguation":
                candidates = _search_titles(query)
                return {
                    "ok": False,
                    "error": f"'{query}' is a disambiguation page. Try one of: {candidates[:5]}",
                    "error_type": "disambiguation",
                }
            return {
                "ok": True,
                "result": {
                    "title": summary.get("title", query),
                    "summary": summary.get("extract", ""),
                    "description": summary.get("description", ""),
                    "url": summary.get("content_urls", {}).get("desktop", {}).get("page")
                           or f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                },
            }

        if op == "extract":
            data = _get_extract(query)
            if data.get("_not_found"):
                return {
                    "ok": False,
                    "error": f"no Wikipedia page found for '{query}'",
                    "error_type": "not_found",
                }
            content = data["extract"][:MAX_CONTENT_CHARS]
            return {
                "ok": True,
                "result": {
                    "title": data["title"],
                    "content": content,
                    "url": data["url"],
                    "truncated": len(data["extract"]) > MAX_CONTENT_CHARS,
                },
            }

        return {"ok": False, "error": f"unknown op: {op}", "error_type": "bad_input"}

    except requests.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.response.status_code}: {e}", "error_type": "network_error"}
    except requests.RequestException as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "error_type": "network_error"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "error_type": "network_error"}


SPEC = {
    "name": "wikipedia",
    "description": "Knowledge lookup via Wikipedia REST API. Ops: 'search' (returns title/summary/url for a query), 'extract' (returns first 4000 chars of full article text for a specific page title). Always cite returned url in sources. 10s timeout.",
}
