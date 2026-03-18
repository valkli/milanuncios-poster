#!/usr/bin/env python3
"""Find next publishable product with valid image. Skip no-image items."""
import sys, os, json, requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
PRODUCT_DATA = SCRIPT_DIR / 'temp' / 'product_data.json'
NOTION_API_KEY = os.environ.get('NOTION_API_KEY')
MAX_TRIES = 20

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
NOTION_HEADERS = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

def mark_skip(notion_id, reason):
    try:
        r = requests.patch(f'https://api.notion.com/v1/pages/{notion_id}',
            headers=NOTION_HEADERS,
            json={'properties': {'Milanuncios Posted': {'rich_text': [{'text': {'content': reason}}]}}},
            timeout=30)
        return r.status_code == 200
    except:
        return False

def check_image(url):
    try:
        r = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
        if r.status_code == 200:
            return True
        # Try GET if HEAD fails
        r = requests.get(url, headers=HEADERS, timeout=15, stream=True)
        ct = r.headers.get('Content-Type', '')
        return r.status_code == 200 and 'image' in ct
    except:
        return False

for attempt in range(MAX_TRIES):
    # Fetch next product
    result = os.popen(f'cd /d C:/Users/Val/.openclaw/workspace && python milanuncios-poster/fetch_product_for_milanuncios.py 2>&1').read()
    last_line = [l for l in result.strip().split('\n') if l.strip()][-1]
    
    if 'NO_PRODUCTS' in last_line:
        print('NO_PRODUCTS')
        sys.exit(0)
    
    if not last_line.startswith('OK '):
        print(f'ERROR: {last_line}')
        sys.exit(1)
    
    # Read product data
    with open(PRODUCT_DATA, encoding='utf-8') as f:
        data = json.load(f)
    
    notion_id = data['notion_id']
    images = data['properties'].get('Image') or []
    in_stock = data['properties'].get('In Stock', True)
    name = data['properties'].get('Name', '')[:60]
    
    print(f'[{attempt+1}] Checking: {name}', file=sys.stderr)
    
    # Check stock
    if not in_stock:
        print(f'  → In Stock=False, skipping', file=sys.stderr)
        mark_skip(notion_id, 'NO-STOCK-SKIP')
        continue
    
    # Check images
    if not images:
        print(f'  → No images, skipping', file=sys.stderr)
        mark_skip(notion_id, 'NO-IMAGE-SKIP')
        continue
    
    # Try to access image
    valid_img = None
    for img_url in images:
        print(f'  Trying image: {img_url[:60]}', file=sys.stderr)
        if check_image(img_url):
            valid_img = img_url
            print(f'  → Image OK!', file=sys.stderr)
            break
        else:
            print(f'  → Image failed', file=sys.stderr)
    
    if not valid_img:
        print(f'  → All images failed, skipping', file=sys.stderr)
        mark_skip(notion_id, 'NO-IMAGE-SKIP')
        continue
    
    # Found valid product!
    print(last_line)
    sys.exit(0)

print('NO_PRODUCTS_AFTER_TRIES')
sys.exit(0)
