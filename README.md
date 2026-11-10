# لقطة — Laqta

Saudi shopping aggregator: trending products from Amazon.sa, Noon, Shein, AliExpress, Namshi and Temu
in one app, with price comparison and cashback.

```
collector/   pulls products from the stores, ranks them, writes the app's product file
web/         the live app (works on phones and desktop, installable to the home screen)
data/        the product database, kept between runs (price history, trends)
.github/     the robot that updates everything every 3 hours
netlify.toml settings if you ever host on Netlify instead
```

## How it runs by itself

```
every 3 hours (GitHub Actions)
  → collect products from every connected store
  → rank trending + match the same product across stores
  → write web/data/products.json and save it to this repository
  → publish web/ to GitHub Pages: https://asayedhalim91-sudo.github.io/laqta/
```

Nothing runs on your computer. GitHub Actions and GitHub Pages are free for public repositories.

## One-time setup

1. **GitHub:** create a new repository (private is fine) and upload this whole folder,
   including the hidden `.github` folder.
2. **GitHub Pages:** *Settings* → *Pages* → *Build and deployment* → *Source*: **GitHub Actions**.
3. **First update:** in GitHub open *Actions* → *Update products* → *Run workflow*.
4. **Your own domain (optional):** *Settings* → *Pages* → *Custom domain*, e.g. `laqta.sa`.

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
| Variable | `LAQTA_DEMO` | Sample products are off by default. Set to `1` only to preview the app with fake data |

## Hand-picked products (before a store's API is connected)

`collector/curated/amazon.json` is the list of popular products the app shows today. Each one opens
Amazon.sa with your Associates tag, so purchases earn commission. No price is shown for them (Amazon only
allows prices that come from its API). Edit the file to add, remove or reorder products; add `"asin": "B0…"`
to link straight to one product page instead of a search. The list switches off by itself once the Amazon
API credentials are added.

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
