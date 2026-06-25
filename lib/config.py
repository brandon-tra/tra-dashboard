# lib/config.py
# Central config for the TRA dashboard

# Add Metricool account slugs or IDs here to exclude them from the dashboard.
# Find the slug in the Metricool URL when viewing that account.
EXCLUDED_ACCOUNT_IDS = [
    # "example-client-slug",
]

# Metricool API base URL
METRICOOL_BASE_URL = "https://app.metricool.com/api"

# Networks to pull from Metricool (comment out any you don't need)
METRICOOL_NETWORKS = [
    "instagram",
    "facebook",
    "linkedin",
    "twitter",
    "tiktok",
]
