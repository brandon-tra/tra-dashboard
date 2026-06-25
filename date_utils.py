# lib/date_utils.py
# Converts frontend range tokens into (start_date, end_date) tuples.
# All dates returned as YYYY-MM-DD strings.

from datetime import date, timedelta
import calendar


def resolve_range(range_token: str) -> tuple[str, str]:
    """
    Accepts a range token from the frontend and returns (start_date, end_date).

    Supported tokens:
        7d              → last 7 days
        30d             → last 30 days
        90d             → last 90 days
        month_current   → 1st of this month → today
        month_previous  → 1st → last day of previous month
    """
    today = date.today()

    if range_token == "7d":
        start = today - timedelta(days=7)
        return start.isoformat(), today.isoformat()

    if range_token == "30d":
        start = today - timedelta(days=30)
        return start.isoformat(), today.isoformat()

    if range_token == "90d":
        start = today - timedelta(days=90)
        return start.isoformat(), today.isoformat()

    if range_token == "month_current":
        start = today.replace(day=1)
        return start.isoformat(), today.isoformat()

    if range_token == "month_previous":
        first_of_this_month = today.replace(day=1)
        last_of_prev = first_of_this_month - timedelta(days=1)
        first_of_prev = last_of_prev.replace(day=1)
        return first_of_prev.isoformat(), last_of_prev.isoformat()

    raise ValueError(f"Unknown range token: '{range_token}'. "
                     f"Valid options: 7d, 30d, 90d, month_current, month_previous")
