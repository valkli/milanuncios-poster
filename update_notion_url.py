#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_notion_url.py
Updates a Notion product page with the published Milanuncios URL.

Usage:
  python update_notion_url.py <notion_id> <milanuncios_url>
  python update_notion_url.py  ← reads notion_id from temp/product_data.json + asks for URL via stdin

Examples:
  python update_notion_url.py 2bd12f74-xxxx https://www.milanuncios.com/anuncios/r583687719.htm
"""

import os
import sys
import json
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

NOTION_API_KEY = os.getenv('NOTION_API_KEY')
HEADERS = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

PRODUCT_DATA_FILE = Path(__file__).parent / 'temp' / 'product_data.json'


def update_notion(notion_id: str, milanuncios_url: str) -> bool:
    """Update Notion page with published URL in both fields."""
    payload = {
        'properties': {
            'Milanuncios Posted': {
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {
                            'content': milanuncios_url,
                            'link': {'url': milanuncios_url}
                        }
                    }
                ]
            }
        }
    }

    resp = requests.patch(
        f'https://api.notion.com/v1/pages/{notion_id}',
        headers=HEADERS,
        json=payload
    )

    if resp.status_code == 200:
        print(f'OK Updated: {notion_id} → {milanuncios_url}')
        return True
    else:
        print(f'ERROR {resp.status_code}: {resp.text[:300]}')
        return False


def main():
    notion_id = None
    milanuncios_url = None

    # Mode 1: both args passed on command line
    if len(sys.argv) == 3:
        notion_id = sys.argv[1].strip()
        milanuncios_url = sys.argv[2].strip()

    # Mode 2: read notion_id from product_data.json, url from arg
    elif len(sys.argv) == 2:
        milanuncios_url = sys.argv[1].strip()
        if PRODUCT_DATA_FILE.exists():
            with open(PRODUCT_DATA_FILE, encoding='utf-8') as f:
                data = json.load(f)
            notion_id = data.get('notion_id')
        else:
            print('ERROR: product_data.json not found and no notion_id provided')
            sys.exit(1)

    # Mode 3: read both from product_data.json (url must be passed via stdin or env)
    elif len(sys.argv) == 1:
        if PRODUCT_DATA_FILE.exists():
            with open(PRODUCT_DATA_FILE, encoding='utf-8') as f:
                data = json.load(f)
            notion_id = data.get('notion_id')
            # Try to read url from env variable (set by publishing step)
            milanuncios_url = os.getenv('MILANUNCIOS_URL')
            if not milanuncios_url:
                print('ERROR: MILANUNCIOS_URL env variable not set')
                print('Usage: MILANUNCIOS_URL=https://... python update_notion_url.py')
                print('   or: python update_notion_url.py <notion_id> <url>')
                sys.exit(1)
        else:
            print('ERROR: product_data.json not found')
            sys.exit(1)

    else:
        print('Usage: python update_notion_url.py [notion_id] <milanuncios_url>')
        sys.exit(1)

    if not notion_id:
        print('ERROR: notion_id is empty')
        sys.exit(1)

    if not milanuncios_url or not milanuncios_url.startswith('http'):
        print(f'ERROR: invalid URL: {milanuncios_url}')
        sys.exit(1)

    success = update_notion(notion_id, milanuncios_url)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
