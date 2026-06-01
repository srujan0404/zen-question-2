import wikipedia

MAX_CONTENT_CHARS = 4000


def run(args: dict) -> dict:
    op = args.get("op", "search")
    query = args.get("query") or args.get("page")
    if not query:
        return {"ok": False, "error": "missing 'query' or 'page'", "error_type": "bad_input"}

    try:
        if op == "search":
            wikipedia.search(query)
            page = wikipedia.page(query, auto_suggest=True, redirect=True)
            return {
                "ok": True,
                "result": {
                    "title": page.title,
                    "summary": page.summary,
                    "url": page.url,
                },
            }

        if op == "extract":
            page = wikipedia.page(query, auto_suggest=True, redirect=True)
            content = page.content[:MAX_CONTENT_CHARS]
            return {
                "ok": True,
                "result": {
                    "title": page.title,
                    "content": content,
                    "url": page.url,
                    "truncated": len(page.content) > MAX_CONTENT_CHARS,
                },
            }

        return {"ok": False, "error": f"unknown op: {op}", "error_type": "bad_input"}

    except wikipedia.exceptions.DisambiguationError as e:
        return {
            "ok": False,
            "error": f"ambiguous query '{query}'. Options: {e.options[:5]}. Re-query with a specific title.",
            "error_type": "disambiguation",
        }
    except wikipedia.exceptions.PageError:
        return {"ok": False, "error": f"no Wikipedia page found for '{query}'", "error_type": "not_found"}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "error_type": "network_error"}


SPEC = {
    "name": "wikipedia",
    "description": "Knowledge lookup. Ops: 'search' (returns title/summary/url), 'extract' (returns first 4000 chars of content). Always cite returned url in sources.",
}
