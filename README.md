# لقطة — Laqta

Saudi shopping aggregator: trending products from Amazon.sa, Noon, Shein, AliExpress, Namshi and Temu
in one app, with price comparison and cashback.

```
collector/   pulls products from the stores, ranks them, writes the app's product file
web/         the live app (works on phones and desktop, installable to the home screen)
data/        the product database, kept between runs (price history, trends)
.github/     the robot that updates everything every 3 hours
netlify.toml tells Netlify to publish web/
```

## How it runs by itself

```
every 3 hours (GitHub Actions)
  → collect products from every connected store
  → rank trending + match the same product across stores
  → write web/data/products.json and save it to this repository
  → Netlify sees the change and publishes the app (about 30 seconds)
```

Nothing runs on your computer. GitHub Actions and Netlify are free at this size.

## One-time setup

1. **GitHub:** create a new repository (private is fine) and upload this whole folder,
   including the hidden `.github` folder.
2. **Netlify:** open the project **laqta-sa** → *Project configuration* → *Build & deploy* →
   *Link repository* → choose this repository. Leave build settings empty; `netlify.toml` sets them.
3. **First update:** in GitHub open *Actions* → *Update products* → *Run workflow*.

## Connect the real stores (when your affiliate accounts are approved)

In GitHub: *Settings* → *Secrets and variables* → *Actions*.

| Type | Name | What to put |
|---|---|---|
| Secret | `ALIEXPRESS_APP_KEY`, `ALIEXPRESS_APP_SECRET`, `ALIEXPRESS_TRACKING_ID` | From open.aliexpress.com and portals.aliexpress.com |
| Variable | `AMAZON_PARTNER_TAG` | Your Amazon.sa Associates tag (e.g. `laqta-21`). Works right away on Amazon links. |
| Secret | `AMAZON_CREDENTIAL_ID`, `AMAZON_CREDENTIAL_SECRET` | Creators API credentials (Amazon gives these after your first qualifying sales) |
| Variable | `AMAZON_CREDENTIAL_VERSION` | The version shown next to the credentials (default `3.2`) |
| Secret | `LAQTA_FEED_SOURCES` | Feed links from affiliate networks for Noon, Shein, Namshi, Temu, as JSON: `{"noon": "https://…", "shein": "https://…"}` |
| Variable | `LAQTA_KEYWORDS` | Optional: comma-separated search words for Amazon/AliExpress |
| Variable | `LAQTA_CASHBACK_SHARE` | Optional: share of commission returned as cashback (default `0.5`) |
| Variable | `LAQTA_DEMO` | Set to `0` once real stores are connected, to remove the sample products |

## Work on it locally

```bash
cd collector
pip install -r requirements.txt
python -m pytest -q                      # tests
LAQTA_DB=../data/laqta.db python -m laqta collect
LAQTA_DB=../data/laqta.db python -m laqta export --out ../web/data/products.json
cd ../web && python -m http.server 8000  # open http://localhost:8000
```

More detail on each store and the API: `collector/README.md`.
