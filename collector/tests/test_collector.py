import hashlib
import json

import httpx
import pytest

from laqta.config import Settings
from laqta.connectors.aliexpress import AliExpressConnector, sign_md5
from laqta.connectors.amazon import AmazonConnector
from laqta.connectors.base import guess_category, to_float, to_rate, to_sar
from laqta.connectors.feeds import FeedConnector, row_to_product, store_from_filename
from laqta.db import DB
from laqta.models import Product
from laqta.ranking import compute_trend_scores, match_groups, similarity, tokens


@pytest.fixture
def settings(tmp_path):
    s = Settings()
    s.db_path = str(tmp_path / "t.db")
    s.feeds_dir = str(tmp_path / "feeds")
    s.keywords = ["headphones"]
    return s


# --- helpers -----------------------------------------------------------------------------------
def test_number_parsing():
    assert to_float("1,299.50 SAR") == 1299.5
    assert to_rate("7.0%") == 0.07
    assert to_rate(0.08) == 0.08
    assert to_sar(10, "USD") == 37.5
    assert guess_category("عطر عود فاخر") == "beauty"
    assert guess_category("Crepe Abaya") == "fashion"


# --- AliExpress --------------------------------------------------------------------------------
def test_aliexpress_signature_matches_spec():
    params = {"method": "x", "app_key": "123", "timestamp": "2026-01-01 00:00:00"}
    expected = hashlib.md5(b"SECRETapp_key123methodxtimestamp2026-01-01 00:00:00SECRET").hexdigest().upper()
    assert sign_md5(params, "SECRET") == expected


def test_aliexpress_collect_maps_products(settings):
    settings.ali_app_key, settings.ali_app_secret, settings.ali_tracking_id = "k", "s", "t"
    sent = {}

    def handler(request: httpx.Request):
        form = dict(x.split("=", 1) for x in request.content.decode().split("&"))
        sent.update(form)
        body = {"aliexpress_affiliate_hotproduct_query_response": {"resp_result": {"result": {"products": {"product": [{
            "product_id": 1005001, "product_title": "Wireless Earbuds", "target_sale_price": "10.00",
            "target_sale_price_currency": "USD", "target_original_price": "20.00",
            "promotion_link": "https://s.click.aliexpress.com/e/abc", "lastest_volume": 5400,
            "evaluate_rate": "96.0%", "commission_rate": "9.0%", "product_main_image_url": "https://img/x.jpg"}]}}}}}
        return httpx.Response(200, json=body)

    conn = AliExpressConnector(settings, client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = list(conn.collect())
    assert len(items) == 1
    p = items[0]
    assert p.store == "aliexpress" and p.price == 37.5 and p.old_price == 75.0
    assert p.commission_rate == 0.09 and p.sales == 5400 and p.is_hot and p.rating == 4.8
    assert p.category == "tech"
    assert "sign" in sent and sent["tracking_id"] == "t"


def test_aliexpress_falls_back_when_hot_products_not_allowed(settings):
    settings.ali_app_key, settings.ali_app_secret, settings.ali_tracking_id = "k", "s", "t"

    def handler(request: httpx.Request):
        if b"hotproduct" in request.content:
            return httpx.Response(200, json={"error_response": {"code": "InsufficientPermission"}})
        return httpx.Response(200, json={"aliexpress_affiliate_product_query_response": {"resp_result": {"result": {
            "products": {"product": [{"product_id": 9, "product_title": "Desk Lamp", "target_sale_price": "5",
                                      "promotion_link": "https://s.click.aliexpress.com/e/z"}]}}}}})

    conn = AliExpressConnector(settings, client=httpx.Client(transport=httpx.MockTransport(handler)))
    items = list(conn.collect())
    assert [p.external_id for p in items] == ["9"] and not items[0].is_hot


# --- Amazon ------------------------------------------------------------------------------------
def test_amazon_token_and_search(settings):
    settings.amazon_client_id, settings.amazon_client_secret, settings.amazon_partner_tag = "id", "sec", "laqta-21"
    calls = []

    def handler(request: httpx.Request):
        calls.append(request)
        if "auth/o2/token" in str(request.url):
            body = json.loads(request.content)
            assert body["scope"] == "creatorsapi::default" and body["grant_type"] == "client_credentials"
            return httpx.Response(200, json={"access_token": "TOKEN", "expires_in": 3600})
        assert request.headers["authorization"] == "Bearer TOKEN"
        assert request.headers["x-marketplace"] == "www.amazon.sa"
        body = json.loads(request.content)
        assert body["partnerTag"] == "laqta-21"
        return httpx.Response(200, json={"searchResult": {"items": [{
            "asin": "B0TEST", "detailPageURL": "https://www.amazon.sa/dp/B0TEST?tag=laqta-21",
            "itemInfo": {"title": {"displayValue": "Noise Cancelling Headphones"}},
            "images": {"primary": {"large": {"url": "https://m.media-amazon.com/x.jpg"}}},
            "offersV2": {"listings": [{"price": {"money": {"amount": 189.0, "currency": "SAR"},
                                                 "savingBasis": {"money": {"amount": 289.0, "currency": "SAR"}}}}]},
            "browseNodeInfo": {"websiteSalesRank": {"salesRank": 42}},
            "customerReviews": {"count": 1200, "starRating": {"value": 4.6}}}]}})

    conn = AmazonConnector(settings, client=httpx.Client(transport=httpx.MockTransport(handler)))
    conn.collect = lambda: (p for item in conn.search("headphones") if (p := conn.to_product(item)))  # skip sleep
    items = list(conn.collect())
    assert "api.amazon.co.uk" in str(calls[0].url)  # credential version 3.2 by default
    p = items[0]
    assert (p.external_id, p.price, p.old_price, p.sales_rank, p.is_hot) == ("B0TEST", 189.0, 289.0, 42, True)
    assert "tag=laqta-21" in p.url


# --- feeds -------------------------------------------------------------------------------------
def test_feed_file_naming():
    from pathlib import Path
    assert store_from_filename(Path("noon.csv")) == "noon"
    assert store_from_filename(Path("shein_women.csv")) == "shein"
    assert store_from_filename(Path("random.csv")) is None


def test_feed_rows_from_different_networks():
    admitad = {"id": "N1", "name": "عطر عود 100 مل", "price": "320", "oldprice": "450", "currencyid": "SAR",
               "url": "https://ad.admitad.com/g/x", "picture": "https://img/1.jpg"}
    cj = {"sku": "S9", "title": "Maxi Dress", "sale_price": "21 USD", "price": "30 USD", "currency": "USD",
          "link": "https://www.anrdoezrs.net/click", "image_link": "https://img/2.jpg", "is_bestseller": "yes"}
    a = row_to_product(admitad, "noon")
    b = row_to_product(cj, "shein")
    assert (a.price, a.old_price, a.category) == (320.0, 450.0, "beauty")
    assert (b.price, b.category, b.is_hot) == (78.75, "fashion", True)
    assert row_to_product({"id": "x", "name": "no link", "price": "5"}, "noon") is None


def test_feed_connector_reads_csv_json_xml(settings, tmp_path):
    d = tmp_path / "feeds"
    d.mkdir()
    (d / "noon.csv").write_text("id,name,price,url\n1,Smart Watch,249,https://a/1\n2,Air Fryer,229,https://a/2\n",
                                encoding="utf-8")
    (d / "namshi.json").write_text(json.dumps({"products": [{"id": "z", "title": "Oud", "price": 300,
                                                             "deeplink": "https://a/z"}]}), encoding="utf-8")
    (d / "temu.xml").write_text("<yml_catalog><shop><offers><offer id='t1'><name>LED Lamp</name><price>45</price>"
                                "<url>https://a/t1</url></offer></offers></shop></yml_catalog>", encoding="utf-8")
    items = list(FeedConnector(settings).collect())
    assert sorted(p.uid for p in items) == ["namshi:z", "noon:1", "noon:2", "temu:t1"]


# --- storage, ranking, matching ----------------------------------------------------------------
def _p(store, ext, title, price, **kw):
    return Product(store=store, external_id=ext, title=title, price=price, url=f"https://x/{store}/{ext}", **kw)


def test_velocity_ranking_and_matching(settings):
    db = DB(settings.db_path)
    db.upsert([_p("amazon", "a", "Wireless Noise Cancelling Headphones", 189, sales=100, category="tech"),
               _p("amazon", "b", "Digital Air Fryer 5.5L", 229, sales=100, category="home")])
    # fake: first run was 2 days ago
    db.conn.execute("UPDATE products SET last_seen=datetime('now','-2 days')||'+00:00', "
                    "first_seen=datetime('now','-10 days')||'+00:00'")
    db.conn.commit()
    db.upsert([_p("amazon", "a", "Wireless Noise Cancelling Headphones", 179, sales=900, category="tech"),
               _p("amazon", "b", "Digital Air Fryer 5.5L", 229, sales=110, category="home"),
               _p("noon", "n1", "Noise Cancelling Wireless Headphones", 199, category="tech")])
    v = {r["uid"]: r["sales_velocity"] for r in db.rows("SELECT uid, sales_velocity FROM products")}
    assert round(v["amazon:a"]) == 400 and round(v["amazon:b"]) == 5

    compute_trend_scores(db)
    top = db.rows("SELECT uid FROM products WHERE store='amazon' ORDER BY trend_score DESC")
    assert top[0]["uid"] == "amazon:a"

    assert match_groups(db) == 1
    g = {r["uid"]: r["group_id"] for r in db.rows("SELECT uid, group_id FROM products")}
    assert g["amazon:a"] == g["noon:n1"] != g["amazon:b"]
    assert db.lowest_price("amazon:a") == 179


def test_similarity_ignores_noise_words():
    assert similarity(tokens("New Wireless Headphones for Men"), tokens("wireless headphones")) == 1.0


# --- API end to end on demo data ---------------------------------------------------------------
def test_api_end_to_end(settings, monkeypatch):
    from laqta.collector import run
    summary = run(settings, demo=True)
    assert summary["sources"]["demo"] > 20 and summary["matched_groups"] >= 8

    monkeypatch.setenv("LAQTA_DB", settings.db_path)
    import importlib
    import laqta.api as api
    importlib.reload(api)
    from fastapi.testclient import TestClient
    client = TestClient(api.app)

    t = client.get("/trending", params={"limit": 5}).json()["items"]
    assert len(t) == 5 and t[0]["rank"] == 1
    assert len({i["group_id"] for i in t}) == 5          # one card per product
    assert "commission_rate" not in t[0] and t[0]["cashback"] > 0
    abaya = [i for i in client.get("/search", params={"q": "عباية"}).json()["items"]]
    assert abaya[0]["store_count"] == 2                  # shein + namshi, even beyond the loaded page

    detail = client.get(f"/products/{t[0]['uid']}").json()
    nets = [o["net_price"] for o in detail["offers"]]
    assert len(nets) >= 2 and nets == sorted(nets) and detail["offers"][0]["best"]

    assert client.get("/search", params={"q": "عود"}).json()["items"]
    assert client.get("/trending", params={"category": "fashion"}).json()["items"][0]["category"] == "fashion"
    assert client.get("/trending", params={"store": "nope"}).status_code == 400
    assert client.get("/health").json()["active_products"] > 20


# --- hand-picked products (before the Amazon API is connected) -----------------------------------
def test_curated_products_link_with_tag_and_show_no_price(settings, tmp_path):
    from laqta.collector import run
    from laqta.export import build
    settings.amazon_partner_tag = "laqta-21"
    settings.amazon_client_id = settings.amazon_client_secret = ""
    settings.curated_dir = str(tmp_path / "curated")
    (tmp_path / "curated").mkdir()
    (tmp_path / "curated" / "amazon.json").write_text(json.dumps([
        {"id": "a", "title": "سماعات أبل", "title_en": "Apple AirPods Pro", "query": "Apple AirPods Pro", "category": "tech"},
        {"id": "b", "title": "عطر", "query": "عطر عود", "category": "beauty", "asin": "B0TEST1234"},
    ], ensure_ascii=False), encoding="utf-8")

    run(settings, demo=True)                      # sample products present…
    summary = run(settings, demo=False)           # …and gone the moment demo is switched off
    assert summary["sources"]["curated"] == 2
    data = build(DB(settings.db_path), settings)
    assert data["sample"] is False and data["priced"] is False
    assert [p["title"] for p in data["products"]] == ["سماعات أبل", "عطر"]   # file order kept
    a, b = (p["offers"][0] for p in data["products"])
    assert a["url"] == "https://www.amazon.sa/s?k=Apple+AirPods+Pro&tag=laqta-21"
    assert b["url"] == "https://www.amazon.sa/dp/B0TEST1234?tag=laqta-21"
    assert a["price"] is None and a["net_price"] is None and a["cashback"] == 0 and a["history"] == []
    assert data["products"][0]["price"] is None and data["products"][0]["max_cashback"] == 0
