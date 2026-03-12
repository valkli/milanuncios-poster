#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_sold_products.py
Finds products that are SOLD (In Stock=False) but still have a Milanuncios URL.
Works across both Notion DBs.

Usage:
  python cleanup_sold_products.py            # list sold products
  python cleanup_sold_products.py --clear <notion_id>   # clear URL in Notion
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
DB_IDS = [db for db in [DB1_ID, DB2_ID] if db]

HEADERS = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

OUT_DIR = Path(__file__).parent / 'temp'
OUT_FILE = OUT_DIR / 'sold_products.json'


def fetch_sold_from_db(db_id):
    """Query one DB for sold products that still have a Milanuncios ad URL."""
    results = []
    cursor = None
    while True:
        payload = {
            "filter": {
                "and": [
                    {"property": "In Stock", "checkbox": {"equals": False}},
                    {"property": "Milanuncios Posted", "rich_text": {"is_not_empty": True}}
                ]
            },
            "page_size": 100
        }
        if cursor:
            payload["start_cursor"] = cursor

        resp = requests.post(
            f'https://api.notion.com/v1/databases/{db_id}/query',
            headers=HEADERS, json=payload
        )
        if resp.status_code != 200:
            print(f'ERROR: DB {db_id} → {resp.status_code}: {resp.text[:100]}', file=sys.stderr)
            break

        data = resp.json()
        for page in data.get('results', []):
            props = page['properties']
            name = ''
            if props.get('Name', {}).get('title'):
                name = props['Name']['title'][0]['text']['content']
            milan_url = ''
            rt = props.get('Milanuncios Posted', {}).get('rich_text', [])
            if rt:
                milan_url = rt[0]['text']['content']
            if milan_url:
                results.append({
                    'notion_id': page['id'],
                    'name': name,
                    'milanuncios_url': milan_url
                })

        if not data.get('has_more'):
            break
        cursor = data.get('next_cursor')

    return results


def clear_notion_url(notion_id: str) -> bool:
    """Clear the Milanuncios Posted field in Notion (product sold, ad deleted)."""
    payload = {
        'properties': {
            'Milanuncios Posted': {'rich_text': []}
        }
    }
    resp = requests.patch(
        f'https://api.notion.com/v1/pages/{notion_id}',
        headers=HEADERS,
        json=payload
    )
    if resp.status_code == 200:
        print(f'OK Cleared: {notion_id}', file=sys.stderr)
        return True
    else:
        print(f'ERROR {resp.status_code}: {resp.text[:200]}', file=sys.stderr)
        return False


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Mode: --clear <notion_id>
    if len(sys.argv) == 3 and sys.argv[1] == '--clear':
        notion_id = sys.argv[2]
        success = clear_notion_url(notion_id)
        sys.exit(0 if success else 1)

    # Mode: list sold products across all DBs
    all_sold = []
    for db_id in DB_IDS:
        all_sold.extend(fetch_sold_from_db(db_id))

    # Only real Milanuncios URLs (skip "Yes"/"YES" garbage)
    real_url = [p for p in all_sold if p['milanuncios_url'].startswith('https://www.milanuncios.com')]

    result = {
        'count': len(real_url),
        'need_browser_delete': real_url,
    }

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
