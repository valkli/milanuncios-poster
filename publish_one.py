#!/usr/bin/env python3
"""Publish one product from Notion to Milanuncios via CDP"""
import asyncio, websockets, json, sys, io, urllib.request, time, subprocess, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGET_ID = "23FA8579BE4846FC66E7D1C48EF687E9"
WS = f"ws://127.0.0.1:18800/devtools/page/{TARGET_ID}"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

mid = 0
def nid():
    global mid; mid += 1; return mid

async def send(ws, method, params={}):
    cmd = {'id': nid(), 'method': method, 'params': params}
    await ws.send(json.dumps(cmd))
    while True:
        r = json.loads(await ws.recv())
        if r.get('id') == cmd['id']: return r

async def js(ws, expr):
    r = await send(ws, 'Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
    return r.get('result', {}).get('result', {}).get('value', '')

async def main():
    # Load product data
    data_file = os.path.join(SCRIPT_DIR, 'temp', 'product_data.json')
    with open(data_file, encoding='utf-8') as f:
        data = json.load(f)
    p = data['properties']
    
    name = p.get('Name','').replace('\\(','(').replace('\\)',')')
    title = name[:60] if len(name) > 60 else name
    desc = f"{name}. En perfecto estado. Producto de segunda mano en buen estado."
    price = str(int(p.get('Selling Price', 5)))
    notion_id = data['notion_id']
    
    print(f"Publishing: {title[:50]}...")
    print(f"Price: {price}€, Notion ID: {notion_id}")
    
    async with websockets.connect(WS, max_size=10*1024*1024) as ws:
        # Navigate to publish form
        await send(ws, 'Page.navigate', {'url': 'https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447'})
        await asyncio.sleep(4)
        page_title = await js(ws, 'document.title')
        print(f"Page: {page_title[:50]}")
        
        # Inject photo via separate script
        print("Injecting photo...")
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, 'inject_photo_cdp.py')],
            capture_output=True, text=True, cwd=SCRIPT_DIR
        )
        print("Photo:", result.stdout.strip()[-50:] if result.stdout else result.stderr.strip()[-50:])
        await asyncio.sleep(1)
        
        # Fill title
        r = await js(ws, f"""(function(){{
            var el = document.querySelector('input#title');
            if(!el) return 'NF';
            el.focus();
            el.select();
            document.execCommand('insertText', false, {json.dumps(title)});
            return 'OK:' + el.value.length;
        }})()""")
        print(f"Title: {r}")
        await asyncio.sleep(0.3)
        
        # Fill description
        r = await js(ws, f"""(function(){{
            var el = document.querySelector('textarea#description');
            if(!el) return 'NF';
            el.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);
            document.execCommand('insertText', false, {json.dumps(desc)});
            return 'OK:' + el.value.length;
        }})()""")
        print(f"Desc: {r}")
        await asyncio.sleep(0.3)
        
        # Set Estado = Prácticamente nuevo
        r = await js(ws, """(function(){
            var all = document.querySelectorAll('*');
            for(var el of all){
                if(el.childElementCount === 0 && el.textContent.trim() === 'Pr\u00e1cticamente nuevo'){
                    el.click(); return 'OK';
                }
            }
            return 'NF';
        })()""")
        print(f"Estado: {r}")
        await asyncio.sleep(0.3)
        
        # Fill price
        r = await js(ws, f"""(function(){{
            var el = document.querySelector('input[type="number"]');
            if(!el) return 'NF';
            el.focus();
            el.select();
            document.execCommand('insertText', false, '{price}');
            return 'OK';
        }})()""")
        print(f"Price: {r}")
        await asyncio.sleep(0.3)
        
        # Click Publicar
        r = await js(ws, """(function(){
            var btns = Array.from(document.querySelectorAll('button'));
            for(var b of btns){ if(b.textContent.trim()==='Publicar'){b.click();return 'OK';} }
            return 'NF';
        })()""")
        print(f"Publicar click: {r}")
        await asyncio.sleep(3)
        
        # Handle "sin envio" dialog
        r = await js(ws, """(function(){
            var all = Array.from(document.querySelectorAll('a,button'));
            for(var e of all){
                if(e.textContent.indexOf('sin env') !== -1){ e.click(); return 'OK:' + e.textContent.trim(); }
            }
            return 'no dialog';
        })()""")
        print(f"Sin envio: {r}")
        await asyncio.sleep(5)
        
        # Get URL from mis-anuncios (take the newest = highest r-number)
        await send(ws, 'Page.navigate', {'url': 'https://www.milanuncios.com/mis-anuncios/'})
        await asyncio.sleep(4)
        ad_url = await js(ws, """(function(){
            var links = Array.from(document.querySelectorAll('a[href*="/anuncios/r"]'));
            var urls = links.map(l => l.href).filter(h => h.match(/r\\d+\\.htm/));
            // Sort by number descending, take newest
            urls.sort((a,b) => {
                var na = parseInt(a.match(/r(\\d+)\\.htm/)[1]);
                var nb = parseInt(b.match(/r(\\d+)\\.htm/)[1]);
                return nb - na;
            });
            return urls.length > 0 ? urls[0] : 'not found';
        })()""")
        print(f"Ad URL: {ad_url}")
        
        return ad_url, notion_id

ad_url, notion_id = asyncio.run(main())

if 'milanuncios' in ad_url:
    # Update Notion
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, 'update_notion_url.py'), ad_url],
        capture_output=True, text=True, cwd=SCRIPT_DIR
    )
    print("Notion:", result.stdout.strip()[-100:])
    print(f"\nSUCCESS: {ad_url}")
else:
    print(f"ERROR: Could not get ad URL")
