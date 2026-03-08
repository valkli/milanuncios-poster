#!/usr/bin/env python3
"""
inject_photo_cdp.py
Injects a product image into Milanuncios publish form via Chrome DevTools Protocol.
Works for ANY image URL regardless of CORS restrictions.

Reads:  temp/product_data.json  (for image URL)
        Downloads image to /tmp/openclaw/uploads/product_image.jpg

Usage:
  python inject_photo_cdp.py <cdp_ws_url>
  python inject_photo_cdp.py  (auto-discovers target from http://127.0.0.1:18800)

Output:
  OK files=1     — image injected
  NO_IMAGE       — no image in product_data
  ERROR <reason> — injection failed
"""

import sys
import os
import json
import base64
import asyncio
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR   = Path(__file__).parent
PRODUCT_DATA = SCRIPT_DIR / 'temp' / 'product_data.json'
UPLOADS_DIR  = Path('/tmp/openclaw/uploads')
IMAGE_FILE   = UPLOADS_DIR / 'product_image.jpg'
CDP_BASE     = 'http://127.0.0.1:18800'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}


def download_image():
    """Download product image. Returns (path, url) or (None, None)."""
    if not PRODUCT_DATA.exists():
        print('ERROR product_data.json not found')
        sys.exit(1)

    with open(PRODUCT_DATA, encoding='utf-8') as f:
        data = json.load(f)

    images = data['properties'].get('Image') or []
    if not images:
        print('NO_IMAGE')
        sys.exit(0)

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    for url in images:
        print(f'Trying: {url[:80]}', file=sys.stderr)
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            if 'image' not in r.headers.get('Content-Type', '') and len(r.content) < 1000:
                raise ValueError('Not an image')
            IMAGE_FILE.write_bytes(r.content)
            print(f'Downloaded: {len(r.content)//1024} KB', file=sys.stderr)
            return str(IMAGE_FILE), url
        except Exception as e:
            print(f'  Failed: {e}', file=sys.stderr)

    print('NO_IMAGE')
    sys.exit(0)


def get_milanuncios_ws_url():
    """Find the Milanuncios tab WebSocket URL via CDP /json endpoint."""
    try:
        resp = requests.get(f'{CDP_BASE}/json', timeout=5)
        targets = resp.json()
        for t in targets:
            if 'milanuncios.com' in t.get('url', '') and t.get('type') == 'page':
                return t['webSocketDebuggerUrl']
        print('ERROR: No Milanuncios tab found in CDP targets', file=sys.stderr)
        return None
    except Exception as e:
        print(f'ERROR: Cannot connect to CDP: {e}', file=sys.stderr)
        return None


def build_inject_js(img_path):
    """Build JS function that injects image from base64 into the upload input."""
    data = Path(img_path).read_bytes()
    b64 = base64.b64encode(data).decode()

    js = (
        '() => {'
        f' const b64 = "{b64}";'
        ' const byteChars = atob(b64);'
        ' const bytes = new Uint8Array(byteChars.length);'
        ' for (let i = 0; i < byteChars.length; i++) bytes[i] = byteChars.charCodeAt(i);'
        ' const blob = new Blob([bytes], {type: "image/jpeg"});'
        ' const file = new File([blob], "product.jpg", {type: "image/jpeg"});'
        ' const dt = new DataTransfer();'
        ' dt.items.add(file);'
        ' const input = document.querySelector("#sui-MoleculePhotoUploader-id");'
        ' if (!input) return {ok:false,error:"input not found"};'
        ' const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "files").set;'
        ' nativeSetter.call(input, dt.files);'
        ' input.dispatchEvent(new Event("change", {bubbles:true}));'
        ' input.dispatchEvent(new Event("input", {bubbles:true}));'
        ' const fk = Object.keys(input).find(k => k.startsWith("__reactFiber"));'
        ' if (fk) {'
        '   let fiber = input[fk];'
        '   while (fiber) {'
        '     if (fiber.memoizedProps && fiber.memoizedProps.onChange) {'
        '       fiber.memoizedProps.onChange({target:input,currentTarget:input,'
        '         nativeEvent:new Event("change"),bubbles:true,persist:()=>{},'
        '         preventDefault:()=>{},stopPropagation:()=>{},type:"change"});'
        '       break;'
        '     }'
        '     fiber = fiber.return;'
        '   }'
        ' }'
        ' return {ok:true, files:input.files.length};'
        '}'
    )
    return js


async def inject_via_cdp(ws_url, js_fn):
    """Send evaluate command via CDP WebSocket."""
    import websockets
    async with websockets.connect(ws_url, max_size=10_000_000) as ws:
        cmd = {
            'id': 1,
            'method': 'Runtime.evaluate',
            'params': {
                'expression': f'({js_fn})()',
                'awaitPromise': False,
                'returnByValue': True
            }
        }
        await ws.send(json.dumps(cmd))
        while True:
            resp = await asyncio.wait_for(ws.recv(), timeout=20)
            data = json.loads(resp)
            if data.get('id') == 1:
                return data.get('result', {}).get('result', {}).get('value')


def main():
    # Get CDP WS URL
    if len(sys.argv) > 1:
        ws_url = sys.argv[1]
    else:
        ws_url = get_milanuncios_ws_url()
        if not ws_url:
            print('ERROR: Could not find Milanuncios tab CDP URL')
            sys.exit(1)

    print(f'CDP target: {ws_url}', file=sys.stderr)

    # Download image
    img_path, img_url = download_image()

    # Build and run injection
    js = build_inject_js(img_path)
    print(f'Injecting {len(js)//1024}KB JS...', file=sys.stderr)

    result = asyncio.run(inject_via_cdp(ws_url, js))

    if result and result.get('ok'):
        print(f'OK files={result.get("files", "?")}')
    else:
        err = result.get('error', 'unknown') if result else 'no result'
        print(f'ERROR {err}')
        sys.exit(1)


if __name__ == '__main__':
    main()
