# scripts/test_metricool.py
# Run this directly in PyCharm to test your Metricool connection.
# It prints raw API response so you can see what fields come back.
#
# Usage: python scripts/test_metricool.py [range_token]
# Example: python scripts/test_metricool.py 7d

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from api.metricool import fetch_metricool_data
from lib.date_utils import resolve_range

range_token = sys.argv[1] if len(sys.argv) > 1 else "7d"
start_date, end_date = resolve_range(range_token)
import lib.config as cfg
cfg.EXCLUDED_ACCOUNT_IDS = ["6233634", "6233645", "6233679", "6233690", "6233694", "6241176", "6241182", "6241185", "6241188", "6241208", "6241225", "6241230", "6241303", "6241391", "6241397", "6241398", "6241399", "6241403", "6241521", "6251561", "6251562"]

print(f"\nFetching Metricool data: {start_date} → {end_date}\n")

try:
    data = fetch_metricool_data(start_date, end_date)
    print(json.dumps(data, indent=2))
    print(f"\n✓ {len(data)} account(s) returned")
except Exception as e:
    print(f"\n✗ Error: {e}")
