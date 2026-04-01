#!/usr/bin/env python3
import asyncio, json
import websockets, requests

async def main():
    r = requests.get("http://127.0.0.1:18801/json", timeout=5)
    tabs = r.json()
    ws_url = None
    for t in tabs:
        if "milanuncios.com" in t.get("url","") and t.get("type") == "page":
            ws_url = t["webSocketDebuggerUrl"]
            break
    
    async with websockets.connect(ws_url, max_size=10_000_000) as ws:
        cmd_id = [1]
        
        async def eval_js(js):
            cid = cmd_id[0]; cmd_id[0] += 1
            await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == cid:
                    return msg.get("result",{}).get("result",{}).get("value")
        
        # Navigate fresh
        cid = cmd_id[0]; cmd_id[0] += 1
        await ws.send(json.dumps({"id": cid, "method": "Page.navigate", "params": {"url": "https://www.milanuncios.com/mis-anuncios"}}))
        await asyncio.sleep(4)
        
        js = """(function() {
  var links = Array.from(document.querySelectorAll('a[href*="/anuncios/r"]'));
  return links.slice(0,5).map(l => l.href).join('\\n');
})()"""
        urls = await eval_js(js)
        print("TOP URLS:")
        print(urls)

asyncio.run(main())
