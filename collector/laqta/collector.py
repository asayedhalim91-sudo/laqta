"""Runs every connector that is set up, saves the results, then re-ranks and re-matches."""
from __future__ import annotations

import logging
import traceback

from .config import Settings
from .connectors.aliexpress import AliExpressConnector
from .connectors.amazon import AmazonConnector
from .connectors.base import Connector
from .connectors.demo import DemoConnector
from .connectors.feeds import FeedConnector
from .db import DB
from .models import now_iso
from .ranking import compute_trend_scores, match_groups

log = logging.getLogger(__name__)


def build_connectors(s: Settings, demo: bool) -> list[Connector]:
    out: list[Connector] = []
    if s.amazon_ready:
        out.append(AmazonConnector(s))
    else:
        log.info("Amazon: skipped (set AMAZON_CREDENTIAL_ID, AMAZON_CREDENTIAL_SECRET, AMAZON_PARTNER_TAG)")
    if s.aliexpress_ready:
        out.append(AliExpressConnector(s))
    else:
        log.info("AliExpress: skipped (set ALIEXPRESS_APP_KEY, ALIEXPRESS_APP_SECRET, ALIEXPRESS_TRACKING_ID)")
    out.append(FeedConnector(s))
    if demo:
        out.append(DemoConnector())
    return out


def run(s: Settings | None = None, demo: bool = True, download_feeds: bool = False) -> dict:
    s = s or Settings()
    db = DB(s.db_path)
    summary: dict = {"sources": {}}
    for conn in build_connectors(s, demo):
        started = now_iso()
        try:
            if download_feeds and isinstance(conn, FeedConnector):
                conn.download()
            # De-duplicate within a run (the same item can come back for two keywords)
            seen = {}
            for p in conn.collect():
                seen[p.uid] = p
            count = db.upsert(seen.values())
            db.log_run(conn.name, started, count)
            summary["sources"][conn.name] = count
            log.info("%s: saved %d products", conn.name, count)
        except Exception as e:  # noqa: BLE001 - one broken store must not stop the others
            db.log_run(conn.name, started, 0, error=f"{e}\n{traceback.format_exc(limit=3)}")
            summary["sources"][conn.name] = f"error: {e}"
            log.error("%s failed: %s", conn.name, e)
    summary["hidden_stale"] = db.deactivate_stale()
    summary["ranked"] = compute_trend_scores(db)
    summary["matched_groups"] = match_groups(db)
    return summary
