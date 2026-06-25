# api/ga4.py
# Vercel serverless function — proxies Google Analytics 4 Data API.
# Called by the frontend as: GET /api/ga4?range=30d

import json
import os
import sys

from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.date_utils import resolve_range

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from google.oauth2 import service_account


def get_ga4_client():
    """
    Returns an authenticated GA4 client.
    - Locally: reads from GA4_KEY_PATH (path to JSON file)
    - On Vercel: reads from GA4_SERVICE_ACCOUNT_JSON (JSON string env var)
    """
    json_str = os.environ.get("GA4_SERVICE_ACCOUNT_JSON")
    key_path = os.environ.get("GA4_KEY_PATH")

    if json_str:
        info = json.loads(json_str)
        credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
    elif key_path:
        credentials = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
    else:
        raise EnvironmentError(
            "No GA4 credentials found. Set GA4_SERVICE_ACCOUNT_JSON (Vercel) "
            "or GA4_KEY_PATH (local)."
        )

    return BetaAnalyticsDataClient(credentials=credentials)


def fetch_ga4_data(start_date: str, end_date: str) -> dict:
    """
    Fetches core web metrics from GA4 for the given date range.
    Extend the dimensions/metrics lists below to add more data points.
    """
    property_id = os.environ.get("GA4_PROPERTY_ID")
    if not property_id:
        raise EnvironmentError("GA4_PROPERTY_ID is not set")

    client = get_ga4_client()

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="date"),
            Dimension(name="sessionDefaultChannelGroup"),
        ],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
            Metric(name="newUsers"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
    )

    response = client.run_report(request)

    rows = []
    for row in response.rows:
        rows.append({
            "date": row.dimension_values[0].value,
            "channel": row.dimension_values[1].value,
            "sessions": int(row.metric_values[0].value),
            "active_users": int(row.metric_values[1].value),
            "new_users": int(row.metric_values[2].value),
            "bounce_rate": float(row.metric_values[3].value),
            "avg_session_duration": float(row.metric_values[4].value),
        })

    return {"rows": rows}


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        range_token = params.get("range", ["30d"])[0]

        try:
            start_date, end_date = resolve_range(range_token)
            data = fetch_ga4_data(start_date, end_date)

            body = json.dumps({
                "ok": True,
                "range": range_token,
                "start_date": start_date,
                "end_date": end_date,
                "data": data,
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        except ValueError as e:
            self._error(400, str(e))
        except EnvironmentError as e:
            self._error(500, str(e))
        except Exception as e:
            self._error(502, f"GA4 API error: {e}")

    def _error(self, code: int, message: str):
        body = json.dumps({"ok": False, "error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
