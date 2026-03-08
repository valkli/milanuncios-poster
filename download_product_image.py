#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_product_image.py
Downloads product image from Notion (or external URL) to temp/product_image.jpg.

Reads:  temp/product_data.json  (written by fetch_product_for_milanuncios.py)
Writes: temp/product_image.jpg  (ready for browser upload)

Output:
  OK <path>       — image downloaded, path to file
  NO_IMAGE        — product has no image in Notion
  ERROR <reason>  — download failed
"""

import os
import sys
import json
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
PRODUCT_DATA = SCRIPT_DIR / 'temp' / 'product_data.json'
OUT_DIR      = SCRIPT_DIR / 'temp'
OUT_FILE     = OUT_DIR / 'product_image.jpg'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
}


def try_download(url):
    """Try to download from a URL. Returns (bytes, content_type) or raises."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    ct = resp.headers.get('Content-Type', '')
    if 'image' not in ct and len(resp.content) < 1000:
        raise ValueError(f'Unexpected content-type: {ct}')
    return resp.content, ct


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Also create the uploads dir required by browser.upload
    uploads_dir = Path('/tmp/openclaw/uploads')
    uploads_dir.mkdir(parents=True, exist_ok=True)

    if not PRODUCT_DATA.exists():
        print('ERROR product_data.json not found — run fetch_product_for_milanuncios.py first')
        sys.exit(1)

    with open(PRODUCT_DATA, encoding='utf-8') as f:
        data = json.load(f)

    images = data['properties'].get('Image') or []
    if not images:
        print('NO_IMAGE')
        sys.exit(0)

    # Try each image URL until one downloads successfully
    last_error = None
    for image_url in images:
        print(f'Trying: {image_url[:80]}', file=sys.stderr)
        try:
            content, content_type = try_download(image_url)
            last_error = None
            break
        except Exception as e:
            last_error = str(e)
            print(f'  Failed: {e}', file=sys.stderr)
            continue

    if last_error is not None:
        print(f'ERROR all image URLs failed. Last: {last_error}')
        sys.exit(1)

    # Determine extension
    ext = '.jpg'
    if 'png' in content_type or image_url.lower().endswith('.png'):
        ext = '.png'
    elif 'gif' in content_type or image_url.lower().endswith('.gif'):
        ext = '.gif'

    # Save to temp/ and also to /tmp/openclaw/uploads/ (for browser.upload)
    local_path = OUT_DIR / f'product_image{ext}'
    upload_path = uploads_dir / f'product_image{ext}'
    local_path.write_bytes(content)
    upload_path.write_bytes(content)

    size_kb = len(content) // 1024
    # Output the URL (for JS injection) and the upload path (for browser.upload fallback)
    print(f'OK url={image_url} path={upload_path.resolve()} ({size_kb} KB)')


if __name__ == '__main__':
    main()
