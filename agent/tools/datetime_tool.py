from datetime import date, datetime


def _parse(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def run(args: dict) -> dict:
    op = args.get("op")
    try:
        if op == "today":
            return {"ok": True, "result": date.today().isoformat()}

        if op == "days_between":
            start = _parse(args["start"])
            end = _parse(args["end"])
            return {"ok": True, "result": (end - start).days}

        if op == "years_since":
            d = _parse(args["date"])
            ref_str = args.get("reference")
            ref = _parse(ref_str) if ref_str else date.today()
            years = ref.year - d.year - ((ref.month, ref.day) < (d.month, d.day))
            return {"ok": True, "result": years}

        return {"ok": False, "error": f"unknown op: {op}", "error_type": "bad_input"}

    except (ValueError, KeyError) as e:
        return {"ok": False, "error": str(e), "error_type": "bad_input"}


SPEC = {
    "name": "datetime",
    "description": "Date math. Ops: today, days_between (start, end), years_since (date, optional reference). Dates as YYYY-MM-DD.",
}
