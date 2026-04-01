#!/usr/bin/env python3
"""Check publish status and handle dialogs"""
import asyncio, json
import websockets
import requests

async def check_and_handle():
    r = requests.get("http://127.0.0.1:18801/json", timeout=5)
    tabs = r.json()
    ws_url = None
    page_url = None
    for t in tabs:
        if "milanuncios.com" in t.get("url","") and t.get("type") == "page" and "publicar" in t.get("url",""):
            ws_url = t["webSocketDebuggerUrl"]
            page_url = t["url"]
            break
    if not ws_url:
        print("FORM_GONE")
        for t in tabs:
            if t.get("type") == "page" and "milanuncios" in t.get("url",""):
                print("MA_PAGE:", t["url"])
        return
    
    print("URL:", page_url)
    
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
        
        # Check page state
        title = await eval_js("document.title")
        print("Title:", title)
        
        # Check buttons
        btns = await eval_js("Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim().substring(0,30)).join('|')")
        print("Buttons:", btns)
        
        # Check for enhorabuena
        success = await eval_js("document.body.innerText.includes('Enhorabuena')")
        if success:
            print("STATUS: PUBLISHED_SUCCESS")
            # Get the listing URL from "Ir a mis anuncios" or similar
            ad_url = await eval_js("document.querySelector('a[href*=\"/anuncios/\"]') ? document.querySelector('a[href*=\"/anuncios/\"]').href : 'not found'")
            print("AD_URL:", ad_url)
            return
        
        # Check for dialog "sin envio"
        result = await eval_js("""(function() {
  var btns = Array.from(document.querySelectorAll('button'));
  var noenvio = btns.find(b => b.textContent.toLowerCase().includes('sin env') || b.textContent.toLowerCase().includes('publicar sin'));
  if (noenvio) { noenvio.click(); return 'CLICKED_SIN_ENVIO:' + noenvio.textContent.trim(); }
  return 'NO_DIALOG';
})()""")
        print("Result:", result)
        
        if result and "CLICKED" in result:
            await asyncio.sleep(3)
            success = await eval_js("document.body.innerText.includes('Enhorabuena')")
            if success:
                print("STATUS: PUBLISHED_SUCCESS")
            else:
                title2 = await eval_js("document.title")
                print("STATUS: STILL_ON_PAGE:", title2)

asyncio.run(check_and_handle())
