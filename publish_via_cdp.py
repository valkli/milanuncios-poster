#!/usr/bin/env python3
"""Publish product to Milanuncios via CDP (mixmix profile, port 18801).
Assumes:
- Browser is already on the publish form page
- Photo already injected via inject_photo_cdp.py
- product_data.json contains the product to publish
"""
import asyncio, websockets, json, requests, os, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = Path(__file__).parent
PRODUCT_DATA = SCRIPT_DIR / 'temp' / 'product_data.json'
CDP_BASE = 'http://127.0.0.1:18801'

with open(PRODUCT_DATA, encoding='utf-8') as f:
    data = json.load(f)
p = data['properties']
name = p.get('Name', '').replace('\\(', '(').replace('\\)', ')')
title = name[:60]
desc = f"{name}. En buen estado. Segunda mano."[:300]
price = str(int(p.get('Selling Price', 5)))
notion_id = data['notion_id']

print(f"Publishing: {title[:50]}")
print(f"Price: {price}€  Notion: {notion_id}")

async def publish():
    r = requests.get(f'{CDP_BASE}/json', timeout=5)
    tabs = [t for t in r.json() if 'milanuncios' in t.get('url', '') and t.get('type') == 'page']
    if not tabs:
        print('ERROR: no milanuncios tab found in CDP')
        return None
    ws_url = tabs[0]['webSocketDebuggerUrl']
    print(f"Using tab: {tabs[0]['url'][:60]}", file=sys.stderr)
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        mid = 0
        async def send(method, params={}):
            nonlocal mid; mid += 1
            cmd = {'id': mid, 'method': method, 'params': params}
            await ws.send(json.dumps(cmd))
            while True:
                r2 = json.loads(await ws.recv())
                if r2.get('id') == cmd['id']: return r2
        
        async def js(expr):
            r2 = await send('Runtime.evaluate', {
                'expression': expr,
                'returnByValue': True,
                'awaitPromise': True
            })
            return r2.get('result', {}).get('result', {}).get('value', '')
        
        # Check page
        page_title = await js('document.title')
        print(f"Page: {page_title[:50]}", file=sys.stderr)
        await asyncio.sleep(1)
        
        # Fill title
        title_escaped = json.dumps(title)
        r2 = await js(f"""(function(){{
            var el = document.querySelector('input#title');
            if(!el) return 'NF';
            el.focus(); el.select();
            document.execCommand('insertText', false, {title_escaped});
            return 'OK:' + el.value.length;
        }})()""")
        print(f"Title: {r2}")
        await asyncio.sleep(0.5)
        
        # Fill description
        desc_escaped = json.dumps(desc)
        r2 = await js(f"""(function(){{
            var el = document.querySelector('textarea#description');
            if(!el) return 'NF';
            el.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);
            document.execCommand('insertText', false, {desc_escaped});
            return 'OK:' + el.value.length;
        }})()""")
        print(f"Desc: {r2}")
        await asyncio.sleep(0.5)
        
        # Set estado = Prácticamente nuevo
        r2 = await js(r"""(function(){
            var all = document.querySelectorAll('*');
            for(var el of all){
                if(el.childElementCount === 0 && el.textContent.trim() === 'Pr\u00e1cticamente nuevo'){
                    el.click(); return 'OK';
                }
            }
            return 'NF';
        })()""")
        print(f"Estado: {r2}")
        await asyncio.sleep(0.5)
        
        # Fill price
        r2 = await js(f"""(function(){{
            var el = document.querySelector('input[type=number]');
            if(!el) return 'NF';
            el.focus(); el.select();
            document.execCommand('insertText', false, '{price}');
            return 'OK:' + el.value;
        }})()""")
        print(f"Price: {r2}")
        await asyncio.sleep(0.5)
        
        # Click Publicar
        r2 = await js(r"""(function(){
            var btns = Array.from(document.querySelectorAll('button'));
            for(var b of btns){
                if(b.textContent.trim() === 'Publicar'){b.click(); return 'OK';}
            }
            return 'NF';
        })()""")
        print(f"Publicar: {r2}")
        await asyncio.sleep(4)
        
        # Handle sin envio dialog if it appears
        r2 = await js(r"""(function(){
            var all = Array.from(document.querySelectorAll('a,button'));
            for(var e of all){
                if(e.textContent.indexOf('sin env') !== -1){
                    e.click(); return 'OK:' + e.textContent.trim().substring(0,30);
                }
            }
            return 'no dialog';
        })()""")
        print(f"Sin envio: {r2}")
        await asyncio.sleep(5)
        
        # Navigate to mis-anuncios to get the URL
        await send('Page.navigate', {'url': 'https://www.milanuncios.com/mis-anuncios/'})
        await asyncio.sleep(4)
        
        ad_url = await js(r"""(function(){
            var links = Array.from(document.querySelectorAll('a[href*="/anuncios/r"]'));
            var urls = links.map(l => l.href).filter(h => h.match(/r\d+\.htm/));
            urls.sort(function(a, b){
                var na = parseInt(a.match(/r(\d+)\.htm/)[1]);
                var nb = parseInt(b.match(/r(\d+)\.htm/)[1]);
                return nb - na;
            });
            return urls.length > 0 ? urls[0] : 'not found';
        })()""")
        print(f"Ad URL: {ad_url}")
        return ad_url

ad_url = asyncio.run(publish())

if ad_url and 'milanuncios' in str(ad_url):
    import subprocess
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / 'update_notion_url.py'), notion_id, ad_url],
        capture_output=True, text=True, cwd=str(SCRIPT_DIR)
    )
    print(f"Notion update: {result.stdout.strip()[-100:]}")
    print(f"\nSUCCESS: {ad_url}")
else:
    print(f"ERROR: Could not get ad URL. Got: {ad_url}")
    sys.exit(1)
