# Laqta collector — لقطة

Collects products from Saudi shopping stores, ranks what is trending, matches the same product
across stores for price comparison, and serves it all to the Laqta app and website.

```
Amazon.sa (Creators API) ─┐
AliExpress (Affiliate API) ├─► collector ─► database ─► ranking + matching ─► API ─► app / website
Noon, Shein, Namshi, Temu ─┘   (every few hours)    (price history)
 (affiliate network feeds)
```

## Quick start (works today with sample data)

```bash
pip install -r requirements.txt
python -m laqta collect          # pulls products (sample data until you add accounts)
python -m laqta top              # prints the current top 10
python -m laqta serve            # API at http://localhost:8000  — open /docs to try it
python -m pytest -q              # tests
```

## Connect the real stores

Copy `.env.example` to `.env` and fill in each store as you get approved. Stores you haven't set
up are skipped automatically.

| Store | How it connects | What you need |
|---|---|---|
| **AliExpress** | Official Affiliate API | Join portals.aliexpress.com → create an app on open.aliexpress.com → App Key, App Secret, Tracking ID. Request "Advanced API" to get Hot Products (higher commission). |
| **Amazon.sa** | Official Creators API | Amazon.sa Associates account → Associates Central → Creators API credentials (ID, Secret, Version) + partner tag. Amazon only opens the API after you have qualifying sales, so use normal tagged links until then. |
| **Noon** | Product feed file | Join Noon's affiliate program (e.g. through Arabclicks). Download the product feed. |
| **Shein, Namshi, Temu** | Product feed file | Join each program on its affiliate network (CJ, Admitad, Arabclicks…). Download the product feed. |

**Feeds:** put the files in `feeds/`, named after the store: `noon.csv`, `shein_women.csv`,
`namshi.json`, `temu.xml`. CSV, JSON and XML/YML work, and the usual column names from
Admitad, CJ, Awin and Arabclicks are recognised. If the network gives you a feed URL, copy
`feeds/sources.example.json` to `feeds/sources.json`, paste the URLs and run with `--download`.

When real stores are connected, stop adding sample data:

```bash
python -m laqta collect --no-demo --download
```

## Run it automatically

Run the collector every 3 hours and keep the API running.

**Linux server (cron):**
```
0 */3 * * *  cd /path/to/laqta-collector && python -m laqta collect --no-demo --download >> collect.log 2>&1
```

**Docker:**
```bash
docker build -t laqta .
docker run -d -p 8000:8000 -v laqta-data:/data --env-file .env laqta            # API
docker run --rm -v laqta-data:/data --env-file .env laqta python -m laqta collect --no-demo --download
```

## API (what the app and website call)

| Endpoint | Use |
|---|---|
| `GET /trending?category=&store=&limit=` | Home and "Best sellers" screens. One card per product, with its rank, cashback and how many stores sell it. |
| `GET /deals?min_discount=0.3` | Biggest discounts (White Friday page). |
| `GET /search?q=abaya&sort=trend\|price\|discount` | Search bar. |
| `GET /products/{uid}` | Product screen: every store's offer sorted by price after cashback, price history, lowest in 30 days. |
| `GET /stores`, `GET /categories` | Filter buttons. |
| `GET /health` | Last collection runs and errors. |

Categories: `tech`, `fashion`, `beauty`, `home`, `kids`, `other`.

## How "trending" is decided

Each product gets a score out of 100, compared only with products from the same store
(stores report sales differently). Weights are in `laqta/ranking.py`:

- 35 — selling fast now (sales added since the last run)
- 20 — total sales
- 15 — the store flags it as hot / best seller
- 10 — sales rank (Amazon)
- 10 — discount size
- 5 — rating
- 5 — new in the last 3 days

## Good to know

- **Prices are converted to SAR.** Update `LAQTA_USD_TO_SAR` if the rate moves.
- **Your commission stays private.** The API shows users their cashback, never your commission rate.
- **Matching** groups the same product across stores by title words, category and price.
  It's good for a start; for large catalogs match on model numbers or barcodes (GTIN/EAN) when feeds include them.
- **Only official APIs and feeds.** Don't add scrapers for these stores: it breaks their affiliate
  terms and gets accounts closed.
- **Database:** SQLite (one file) is fine to launch. Move to PostgreSQL when traffic grows.
