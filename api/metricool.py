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

from lib.config import EXCLUDED_ACCOUNT_IDS, METRICOOL_BASE_URL
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
    user_id = os.environ.get("METRICOOL_USER_ID")
    blog_id = os.environ.get("METRICOOL_BLOG_ID")

    if not api_key:
        raise EnvironmentError("METRICOOL_API_KEY is not set")
    if not user_id:
        raise EnvironmentError("METRICOOL_USER_ID is not set")

    headers = {
        "Content-Type": "application/json",
        "X-Mc-Auth": api_key,
    }

    # Step 1: Get all brand/client accounts
    brands_url = f"{METRICOOL_BASE_URL}/admin/simpleProfiles"
    auth_params = {"userId": user_id, "blogId": blog_id}
    brands_resp = requests.get(brands_url, headers=headers, params=auth_params, timeout=15)
    brands_resp.raise_for_status()
    brands = brands_resp.json()

    results = {}

    for brand in brands:
        account_id = str(brand.get("id") or brand.get("blogId"))
        name = brand.get("name", account_id)

        if account_id in EXCLUDED_ACCOUNT_IDS:
            continue

        print(f"  Fetching {name} ({account_id})...")
        account_data = {"name": name, "networks": {}}

        # Instagram posts
        try:
            resp = requests.get(
                f"{METRICOOL_BASE_URL}/v2/analytics/posts/instagram",
                headers=headers,
                params={
                    "userId": user_id,
                    "blogId": account_id,
                    "from": f"{start_date}T00:00:00",
                    "to": f"{end_date}T23:59:59",
                    "timezone": "America/New_York",
                },
                timeout=30,
            )
            resp.raise_for_status()
            ig_data = resp.json()
            account_data["networks"]["instagram"] = ig_data

            # Extract real account name from first post if available
            posts = ig_data.get("data", [])
            if posts and posts[0].get("userId"):
                account_data["name"] = posts[0]["userId"]
        except requests.HTTPError as e:
            account_data["networks"]["instagram"] = {"error": str(e)}

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
