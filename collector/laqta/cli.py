"""Command line:  python -m laqta collect   |   python -m laqta serve   |   python -m laqta top"""
from __future__ import annotations

import argparse
import json
import logging

from .collector import run
from .config import Settings
from .db import DB


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="laqta", description="Collect and rank products from Saudi shopping stores.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="pull products from every store that is set up")
    c.add_argument("--no-demo", action="store_true", help="don't add sample products")
    c.add_argument("--download", action="store_true", help="download feed files listed in feeds/sources.json first")

    s = sub.add_parser("serve", help="start the API for the app and website")
    s.add_argument("--host", default="0.0.0.0")
    s.add_argument("--port", type=int, default=8000)

    e = sub.add_parser("export", help="write products.json for the live web app")
    e.add_argument("--out", default="products.json")

    t = sub.add_parser("top", help="print the current top trending products")
    t.add_argument("-n", type=int, default=10)

    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if args.cmd == "collect":
        print(json.dumps(run(demo=not args.no_demo, download_feeds=args.download), ensure_ascii=False, indent=2))
    elif args.cmd == "export":
        from .export import export
        print(f"Exported {export(args.out)} products to {args.out}")
    elif args.cmd == "serve":
        import uvicorn
        uvicorn.run("laqta.api:app", host=args.host, port=args.port)
    elif args.cmd == "top":
        db = DB(Settings().db_path)
        for r in db.rows("SELECT store, title, price, trend_score FROM products WHERE active=1 "
                         "ORDER BY trend_score DESC LIMIT ?", (args.n,)):
            print(f"{r['trend_score']:6.1f}  {r['store']:<11} {r['price']:>8.2f} SAR  {r['title'][:70]}")


if __name__ == "__main__":
    main()
