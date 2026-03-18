import asyncio, websockets, json, requests, sys
sys.stdout.reconfigure(encoding='utf-8')

async def get_top():
    r = requests.get('http://127.0.0.1:18801/json', timeout=5)
    tabs = [t for t in r.json() if 'milanuncios' in t.get('url','') and t.get('type')=='page']
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
        
        await send('Page.navigate', {'url': 'https://www.milanuncios.com/mis-anuncios/'})
        await asyncio.sleep(4)
        
        r2 = await js('''(function(){
            var arts = document.querySelectorAll("article");
            var res = [];
            for(var a of arts){
                var link = a.querySelector("a[href*='/anuncios/r']");
                var titleText = a.querySelector("a[href*='/anuncios/r']");
                if(link){
                    res.push(link.href + " | " + (link.textContent||"?").trim().substring(0,40));
                }
            }
            res.sort(function(a,b){
                var na = parseInt(a.match(/r(\d+)\.htm/)[1]);
                var nb = parseInt(b.match(/r(\d+)\.htm/)[1]);
                return nb - na;
            });
            return res.slice(0,8).join("\\n");
        })()''')
        print(r2)

asyncio.run(get_top())
