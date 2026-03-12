#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_product_for_milanuncios.py
Fetches the next UNPUBLISHED product from Notion DBs.

Filters:
  - Milanuncios Posted = empty (not yet published)
  - donde = "magazin" OR "sklad"
  - Price > 15 EUR

Sources:
  - DB1: Product_Variants_GangaBox   (2bd12f742f9e8198bfb3dce06af14f58)
  - DB2: Product_Variants_MixMix     (set DB2_ID env var or edit below)

Strategy: alternate between DBs — round-robin per call.
State file: temp/db_cursor.json  {"last_db": 1 or 2}

Saves result to: milanuncios-poster/temp/product_data.json
Prints: OK <product_name> | NO_PRODUCTS
"""

import os
import sys
import json
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

NOTION_API_KEY = os.getenv('NOTION_API_KEY')

DB1_ID = '2bd12f742f9e8198bfb3dce06af14f58'   # Product_Variants_GangaBox
DB2_ID = os.getenv('MILANUNCIOS_DB2_ID', '27f12f742f9e81648959ee3d597c4e7e')  # Second DB

MIN_PRICE = 15.0  # EUR — товары дешевле пропускаем (поле: "Selling Price")

HEADERS = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

OUT_DIR = Path(__file__).parent / 'temp'
OUT_FILE = OUT_DIR / 'product_data.json'
CURSOR_FILE = OUT_DIR / 'db_cursor.json'


def get_next_db_id():
    """Round-robin: alternate between DB1 and DB2."""
    if not DB2_ID:
        return DB1_ID, 1  # only one DB configured

    CURSOR_FILE.parent.mkdir(parents=True, exist_ok=True)
    if CURSOR_FILE.exists():
        try:
            state = json.loads(CURSOR_FILE.read_text())
            last = state.get('last_db', 1)
        except Exception:
            last = 1
    else:
        last = 1

    next_db = 2 if last == 1 else 1
    CURSOR_FILE.write_text(json.dumps({'last_db': next_db}))

    db_id = DB1_ID if next_db == 1 else DB2_ID
    return db_id, next_db


def build_filter():
    """
    Build Notion filter:
      - Milanuncios Posted = empty  (not yet published)
      - donde contains 'magazin' OR 'sklad'  (rich_text field)
      - Selling Price > 15
    """
    return {
        "and": [
            {
                "property": "Milanuncios Posted",
                "rich_text": {"is_empty": True}
            },
            {
                "or": [
                    {"property": "donde", "rich_text": {"contains": "magazin"}},
                    {"property": "donde", "rich_text": {"contains": "sklad"}}
                ]
            },
            {
                "property": "Selling Price",
                "number": {"greater_than": MIN_PRICE}
            }
        ]
    }


def fetch_next_pending(db_id):
    """
    Query Notion for the next product from `db_id` matching all filters.
    Returns first result or None.
    """
    payload = {
        "filter": build_filter(),
        "sorts": [
            {"property": "Created time", "direction": "ascending"}
        ],
        "page_size": 1
    }

    resp = requests.post(
        f'https://api.notion.com/v1/databases/{db_id}/query',
        headers=HEADERS,
        json=payload
    )

    if resp.status_code == 404:
        print(f'ERROR: DB {db_id} not found (check DB2_ID)', file=sys.stderr)
        return None

    if resp.status_code != 200:
        print(f'ERROR: Notion API {resp.status_code}: {resp.text[:200]}')
        sys.exit(1)

    results = resp.json().get('results', [])
    return results[0] if results else None


def fetch_from_any_db():
    """
    Try DB chosen by round-robin. If empty, try the other one.
    Returns (page, db_id) or (None, None).
    """
    db_id, db_num = get_next_db_id()
    page = fetch_next_pending(db_id)

    if page:
        return page, db_id

    # Fallback: try the other DB if DB2 is configured
    if DB2_ID:
        other_id = DB2_ID if db_id == DB1_ID else DB1_ID
        page = fetch_next_pending(other_id)
        if page:
            return page, other_id

    return None, None


def extract_product(page, db_id):
    """Extract relevant fields from a Notion page object."""
    props = page['properties']
    data = {
        'notion_id': page['id'],
        'db_id': db_id,
        'properties': {}
    }

    extractors = {
        'title':        lambda p: p['title'][0]['text']['content'] if p.get('title') else '',
        'rich_text':    lambda p: p['rich_text'][0]['text']['content'] if p.get('rich_text') else '',
        'number':       lambda p: p.get('number'),
        'select':       lambda p: p['select']['name'] if p.get('select') else None,
        'multi_select': lambda p: [s['name'] for s in p.get('multi_select', [])],
        'url':          lambda p: p.get('url'),
        'checkbox':     lambda p: p.get('checkbox'),
        'files':        lambda p: [
            f['file']['url'] if f.get('file') else f['external']['url']
            for f in p.get('files', [])
        ],
    }

    for key, prop in props.items():
        ptype = prop.get('type')
        if ptype in extractors:
            try:
                data['properties'][key] = extractors[ptype](prop)
            except (KeyError, IndexError):
                data['properties'][key] = None

    # Cover image
    if page.get('cover'):
        cover = page['cover']
        if cover.get('external'):
            data['cover_url'] = cover['external']['url']
        elif cover.get('file'):
            data['cover_url'] = cover['file']['url']

    return data


def count_pending(db_id):
    """Count pending products (has_more proxy)."""
    payload = {
        "filter": build_filter(),
        "page_size": 1
    }
    resp = requests.post(
        f'https://api.notion.com/v1/databases/{db_id}/query',
        headers=HEADERS,
        json=payload
    )
    if resp.status_code != 200:
        return '?'
    data = resp.json()
    return '100+' if data.get('has_more') else str(len(data.get('results', [])))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not NOTION_API_KEY:
        print('ERROR: NOTION_API_KEY not set')
        sys.exit(1)

    product, db_id = fetch_from_any_db()

    if not product:
        print('NO_PRODUCTS')
        if OUT_FILE.exists():
            OUT_FILE.unlink()
        sys.exit(0)

    data = extract_product(product, db_id)
    name = data['properties'].get('Name', 'Unknown')
    price = data['properties'].get('Selling Price', 0)
    donde = data['properties'].get('donde', '?')

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    pending = count_pending(db_id)
    db_label = 'DB1' if db_id == DB1_ID else 'DB2'
    print(f'OK {name} | price={price}€ | donde={donde} | {db_label} | remaining~{pending}')


if __name__ == '__main__':
    main()
