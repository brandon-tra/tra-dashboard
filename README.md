# TRA Client Dashboard

Live performance dashboard pulling from **Metricool** (social) and **GA4** (web analytics) for That Random Agency clients.

---

## Architecture

```
GitHub Repo
  ├── /api                  ← Vercel serverless functions (Python)
  │     ├── metricool.py    ← Proxies Metricool REST API
  │     └── ga4.py          ← Proxies GA4 Data API
  ├── /public               ← Static frontend (deployed by Vercel)
  │     └── index.html      ← Dashboard UI
  ├── /scripts              ← Local dev / data exploration scripts
  ├── /lib                  ← Shared helpers (date utils, formatters)
  └── vercel.json           ← Routing config
```

**How it works:** The frontend sends date-range requests to Vercel serverless functions. The functions call Metricool and GA4 using keys stored in Vercel environment variables — keys never touch the repo.

---

## Local Setup (PyCharm)

### 1. Clone and install dependencies

```bash
git clone https://github.com/YOUR_ORG/tra-dashboard.git
cd tra-dashboard
pip install -r requirements.txt
```

### 2. Create your local `.env` file

```bash
cp .env.example .env
```

Then fill in your keys in `.env`:

```
METRICOOL_API_KEY=your_key_here
GA4_PROPERTY_ID=your_property_id_here
GA4_KEY_PATH=./secrets/ga4-service-account.json
```

> **GA4 JSON key:** Place your service account JSON file at `./secrets/ga4-service-account.json`.  
> This folder is gitignored — it never gets committed.

### 3. Run the dev server locally

```bash
vercel dev
```

Or run individual API scripts directly in PyCharm:

```bash
python scripts/test_metricool.py
python scripts/test_ga4.py
```

---

## Vercel Deployment

### Environment variables to add in Vercel dashboard:

| Variable | Description |
|---|---|
| `METRICOOL_API_KEY` | Your Metricool REST API key |
| `GA4_PROPERTY_ID` | GA4 numeric property ID |
| `GA4_SERVICE_ACCOUNT_JSON` | Full contents of your GA4 JSON key (paste as single-line JSON string) |

### Deploy

Push to `main` — Vercel auto-deploys.

```bash
git push origin main
```

---

## Excluded Accounts

To exclude specific Metricool client accounts from the dashboard, edit `lib/config.py`:

```python
EXCLUDED_ACCOUNT_IDS = [
    "account_slug_here",
]
```

---

## Date Range Toggles

The dashboard supports these ranges, all passed as query params to the API functions:

- **7 days** → `?range=7d`
- **30 days** → `?range=30d`
- **90 days** → `?range=90d`
- **Current month** → `?range=month_current`
- **Previous month** → `?range=month_previous`

---

## File Structure

| File | Purpose |
|---|---|
| `api/metricool.py` | Serverless function — fetches social data from Metricool |
| `api/ga4.py` | Serverless function — fetches web analytics from GA4 |
| `lib/config.py` | Shared config (excluded accounts, constants) |
| `lib/date_utils.py` | Date range calculations for each toggle option |
| `public/index.html` | Dashboard frontend |
| `scripts/test_metricool.py` | Local test script — prints raw Metricool response |
| `scripts/test_ga4.py` | Local test script — prints raw GA4 response |
