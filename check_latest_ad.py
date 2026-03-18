import asyncio, websockets, json, requests, sys

async def check(search_term):
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
        
        # Get current page URL
        cur_url = await js('window.location.href')
        print(f"Current page: {cur_url[:70]}")
        
        # Search
        url = f'https://www.milanuncios.com/mis-anuncios?search={search_term.replace(" ", "+")}'
        await send('Page.navigate', {'url': url})
        await asyncio.sleep(4)
        
        results = await js('''(function(){
            var arts = document.querySelectorAll("article");
            var res = [];
            for(var a of arts){
                var link = a.querySelector("a[href*='/anuncios/r']");
                var price = a.querySelector("[class*='price'], p");
                res.push((link ? link.href : '?') + " | " + (link ? (link.textContent||link.innerText||'?').trim().substring(0,40) : '?'));
            }
            return res.join("\\n") || "No results";
        })()''')
        print(results)

search = sys.argv[1] if len(sys.argv) > 1 else "Mars"
asyncio.run(check(search))
