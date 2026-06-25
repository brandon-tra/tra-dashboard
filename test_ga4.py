# scripts/test_ga4.py
# Run this directly in PyCharm to test your GA4 connection.
# It prints the raw rows returned so you can confirm credentials work.
#
# Usage: python scripts/test_ga4.py [range_token]
# Example: python scripts/test_ga4.py month_previous

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from api.ga4 import fetch_ga4_data
from lib.date_utils import resolve_range

range_token = sys.argv[1] if len(sys.argv) > 1 else "7d"
start_date, end_date = resolve_range(range_token)

print(f"\nFetching GA4 data: {start_date} → {end_date}\n")

try:
    data = fetch_ga4_data(start_date, end_date)
    rows = data.get("rows", [])
    print(json.dumps(rows[:10], indent=2))  # Show first 10 rows
    print(f"\n✓ {len(rows)} row(s) returned")
except Exception as e:
    print(f"\n✗ Error: {e}")
