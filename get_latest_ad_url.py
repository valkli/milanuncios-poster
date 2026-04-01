#!/usr/bin/env python3
"""Navigate to mis-anuncios and get latest ad URL"""
import asyncio, json
import websockets
import requests

async def get_url():
    r = requests.get("http://127.0.0.1:18801/json", timeout=5)
    tabs = r.json()
    ws_url = None
    for t in tabs:
        if "milanuncios.com" in t.get("url","") and t.get("type") == "page":
            ws_url = t["webSocketDebuggerUrl"]
            break
    if not ws_url:
        print("ERROR: no milanuncios tab")
        return
    
    async with websockets.connect(ws_url, max_size=10_000_000) as ws:
        cmd_id = [1]
        
        async def eval_js(js):
            cid = cmd_id[0]
            cmd_id[0] += 1
            await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == cid:
                    return msg.get("result", {}).get("result", {}).get("value")
        
        async def navigate(url):
            cid = cmd_id[0]
            cmd_id[0] += 1
            await ws.send(json.dumps({"id": cid, "method": "Page.navigate", "params": {"url": url}}))
            # Wait for navigation
            await asyncio.sleep(4)
        
        # Navigate to mis-anuncios
        await navigate("https://www.milanuncios.com/mis-anuncios")
        
        # Get first ad link
        js = """(function() {
  var links = Array.from(document.querySelectorAll('a[href*="/anuncios/r"]'));
  if (links.length === 0) return "NO_ADS";
  return links[0].href;
})()"""
        url = await eval_js(js)
        print("LATEST_AD_URL:", url)

asyncio.run(get_url())
