import asyncio, websockets, json, requests

async def check():
    r = requests.get('http://127.0.0.1:18801/json', timeout=5)
    tabs = [t for t in r.json() if 'milanuncios' in t.get('url','') and t.get('type')=='page']
    if not tabs: print('No tab'); return
    ws_url = tabs[0]['webSocketDebuggerUrl']
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
            r2 = await send('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
            return r2.get('result', {}).get('result', {}).get('value', '')
        
        # Navigate to search for Xiaomi
        await send('Page.navigate', {'url': 'https://www.milanuncios.com/mis-anuncios?search=Xiaomi'})
        await asyncio.sleep(4)
        
        r2 = await js('''(function(){
            var links = Array.from(document.querySelectorAll("article a"));
            return links.map(l => l.href + " | " + (l.textContent||l.innerText||"?").trim().substring(0,40)).join("\\n");
        })()''')
        print(r2 or 'No results')
        
        # Also get top 3 ads by URL number
        await send('Page.navigate', {'url': 'https://www.milanuncios.com/mis-anuncios/'})
        await asyncio.sleep(4)
        r2 = await js('''(function(){
            var links = Array.from(document.querySelectorAll("article a[href*='/anuncios/r']"));
            var urls = links.map(l => l.href).filter(h => h.match(/r\d+\.htm/));
            urls.sort(function(a, b){
                var na = parseInt(a.match(/r(\d+)\.htm/)[1]);
                var nb = parseInt(b.match(/r(\d+)\.htm/)[1]);
                return nb - na;
            });
            return "Top 5 by ID: " + urls.slice(0,5).join(", ");
        })()''')
        print(r2)

asyncio.run(check())
