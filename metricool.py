# api/metricool.py
# Vercel serverless function — proxies Metricool REST API.
# Called by the frontend as: GET /api/metricool?range=30d

import json
import os
import sys

import requests
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Allow importing from /lib when running locally
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.config import EXCLUDED_ACCOUNT_IDS, METRICOOL_BASE_URL, METRICOOL_NETWORKS
from lib.date_utils import resolve_range

# Load .env locally (Vercel injects env vars automatically in production)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def fetch_metricool_data(start_date: str, end_date: str) -> dict:
    """
    Fetches social performance data from Metricool for all non-excluded accounts.
    Returns a dict keyed by account name.
    """
    api_key = os.environ.get("METRICOOL_API_KEY")
    if not api_key:
        raise EnvironmentError("METRICOOL_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Step 1: Get all brand/client accounts
    brands_url = f"{METRICOOL_BASE_URL}/brands"
    brands_resp = requests.get(brands_url, headers=headers, timeout=15)
    brands_resp.raise_for_status()
    brands = brands_resp.json().get("data", [])

    results = {}

    for brand in brands:
        account_id = brand.get("id") or brand.get("slug")
        name = brand.get("name", account_id)

        # Skip excluded accounts
        if account_id in EXCLUDED_ACCOUNT_IDS:
            continue

        account_data = {"name": name, "networks": {}}

        # Step 2: Fetch stats per network for this brand
        for network in METRICOOL_NETWORKS:
            stats_url = (
                f"{METRICOOL_BASE_URL}/brands/{account_id}/analytics"
                f"?network={network}&start={start_date}&end={end_date}"
            )
            try:
                stats_resp = requests.get(stats_url, headers=headers, timeout=15)
                stats_resp.raise_for_status()
                account_data["networks"][network] = stats_resp.json().get("data", {})
            except requests.HTTPError as e:
                # Network may not be connected for this account — that's fine
                account_data["networks"][network] = {"error": str(e)}

        results[account_id] = account_data

    return results


class handler(BaseHTTPRequestHandler):
    """Vercel expects a class named 'handler' with a do_GET method."""

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        range_token = params.get("range", ["30d"])[0]

        try:
            start_date, end_date = resolve_range(range_token)
            data = fetch_metricool_data(start_date, end_date)

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
        except requests.RequestException as e:
            self._error(502, f"Metricool API error: {e}")

    def _error(self, code: int, message: str):
        body = json.dumps({"ok": False, "error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Suppress default HTTP server logs in Vercel
