#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_milanuncios.py — Audit Milanuncios-published listings in Notion.

Checks ALL published products against current conditions:
  - In Stock = True (must be in stock for Milanuncios)
  - Selling Price > 15
  - donde = "magazin" or "sklad"
  - Page NOT archived/in_trash
  - Sold checkbox NOT True

Products that no longer meet conditions → to_delete (clear Notion field).
For each deleted item, outputs Notion URL so user can manually remove from Milanuncios.

Usage:
    python cleanup_milanuncios.py           # Dry-run: print JSON report
    python cleanup_milanuncios.py --execute # Execute: clear Notion fields for to_delete
"""

import sys
import os
import json
import time
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

NOTION_API_KEY = os.getenv('NOTION_API_KEY', '')
HEADERS = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

DB_GANGABOX = '2bd12f742f9e8198bfb3dce06af14f58'
DB_VARIANTS = '27f12f742f9e81648959ee3d597c4e7e'

VALID_DONDE = {'magazin', 'sklad'}
MIN_PRICE = 15.0


def log(msg):
    print(f'  {msg}', file=sys.stderr, flush=True)


def get_rich_text(prop) -> str:
    if not prop:
        return ''
    items = prop.get('rich_text', [])
    return ''.join(i.get('plain_text', '') for i in items)


def get_number(prop) -> float:
    if not prop:
        return 0.0
    val = prop.get('number')
    return float(val) if val is not None else 0.0


def get_checkbox(prop) -> bool:
    if not prop:
        return False
    return bool(prop.get('checkbox', False))


def get_select(prop) -> str:
    if not prop:
        return ''
    sel = prop.get('select')
    return sel.get('name', '') if sel else ''


def get_title(prop) -> str:
    if not prop:
        return ''
    items = prop.get('title', [])
    return ''.join(i.get('plain_text', '') for i in items)


def query_db_published(db_id: str) -> list:
    url = f'https://api.notion.com/v1/databases/{db_id}/query'
    pages = []
    start_cursor = None

    while True:
        body = {
            'filter': {
                'property': 'Milanuncios Posted',
                'rich_text': {'is_not_empty': True}
            },
            'page_size': 100
        }
        if start_cursor:
            body['start_cursor'] = start_cursor

        try:
            r = requests.post(url, headers=HEADERS, json=body, timeout=30)
            if r.status_code != 200:
                log(f'DB query error {db_id[:8]}: {r.status_code}')
                break
            data = r.json()
            pages.extend(data.get('results', []))
            if not data.get('has_more'):
                break
            start_cursor = data.get('next_cursor')
        except Exception as e:
            log(f'DB query exception: {e}')
            break

    return pages


def classify_page(page: dict) -> dict:
    props = page.get('properties', {})
    archived = page.get('archived', False)
    in_trash = page.get('in_trash', False)

    milanuncios_url = get_rich_text(props.get('Milanuncios Posted'))
    name = get_title(props.get('Name')) or get_rich_text(props.get('Name')) or 'Unknown'
    price = get_number(props.get('Selling Price'))
    donde = get_select(props.get('donde'))
    sold = get_checkbox(props.get('Sold'))
    in_stock = get_checkbox(props.get('In Stock'))

    notion_id = page.get('id', '')
    notion_url = f'https://www.notion.so/kliv/{notion_id.replace("-", "")}'

    base = {
        'notion_id': notion_id,
        'name': name,
        'milanuncios_url': milanuncios_url,
        'notion_url': notion_url,
    }

    # Archived / deleted
    if archived or in_trash:
        return {**base, 'status': 'to_delete', 'reason': 'archived_or_trash'}

    # Sold
    if sold:
        return {**base, 'status': 'to_delete', 'reason': 'sold'}

    # In Stock must be True for Milanuncios (physical stock for in-store/warehouse sales)
    if not in_stock:
        return {**base, 'status': 'to_delete', 'reason': 'out_of_stock'}

    # Price too low
    if price <= MIN_PRICE:
        return {**base, 'status': 'to_delete', 'reason': f'price_too_low ({price})'}

    # donde changed
    if donde and donde.lower() not in VALID_DONDE:
        return {**base, 'status': 'to_delete', 'reason': f'donde_changed ({donde})'}

    return {**base, 'status': 'ok', 'reason': ''}


def clear_notion_fields(notion_id: str) -> bool:
    try:
        r = requests.patch(
            f'https://api.notion.com/v1/pages/{notion_id}',
            headers=HEADERS,
            json={'properties': {
                'Milanuncios Posted': {'rich_text': []}
            }},
            timeout=30
        )
        return r.status_code == 200
    except Exception as e:
        log(f'Update error {notion_id[:8]}: {e}')
        return False


def main():
    execute = '--execute' in sys.argv

    log(f'🧹 Milanuncios Cleanup — {"EXECUTE" if execute else "DRY RUN"}')

    log(f'Querying DB1 (GangaBox)...')
    pages_gb = query_db_published(DB_GANGABOX)
    log(f'Found {len(pages_gb)} published in GangaBox')

    log(f'Querying DB2 (Variants)...')
    pages_v = query_db_published(DB_VARIANTS)
    log(f'Found {len(pages_v)} published in Variants')

    all_pages = pages_gb + pages_v
    log(f'Total: {len(all_pages)} published listings')

    report = {'to_delete': [], 'ok': []}
    for page in all_pages:
        classified = classify_page(page)
        status = classified.pop('status')
        reason = classified.pop('reason', '')
        if status == 'to_delete':
            classified['reason'] = reason
            report['to_delete'].append(classified)
        else:
            report['ok'].append({
                'notion_id': classified['notion_id'],
                'name': classified['name']
            })

    log(f'→ to_delete: {len(report["to_delete"])} | ok: {len(report["ok"])}')

    stats = {'deleted': 0, 'errors': 0}
    if execute and report['to_delete']:
        log('🔧 Executing cleanup...')
        for item in report['to_delete']:
            nid = item['notion_id']
            name = item['name'][:40]
            log(f'🗑 Clearing: {name} ({item["reason"]})')
            if clear_notion_fields(nid):
                stats['deleted'] += 1
            else:
                stats['errors'] += 1
            time.sleep(0.3)
        log(f'✅ Done: deleted={stats["deleted"]} errors={stats["errors"]}')
    elif execute:
        log('✅ Nothing to clean up.')

    report['_stats'] = stats
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
