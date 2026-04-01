#!/usr/bin/env python3
"""Fill Milanuncios form via CDP using websockets (async)"""
import json, time, sys, pathlib, asyncio
import requests
import websockets

PORT = 18801

def get_form_tab_ws():
    r = requests.get(f"http://127.0.0.1:{PORT}/json", timeout=5)
    tabs = r.json()
    for t in tabs:
        if "milanuncios.com/publicar" in t.get("url", "") and t.get("type") == "page":
            return t["webSocketDebuggerUrl"]
    return None

# Load product data
data_file = pathlib.Path("milanuncios-poster/temp/product_data.json")
product = json.loads(data_file.read_text("utf-8"))
props = product["properties"]

title_full = props["Name"].replace("\\-", "-").replace("\\(", "(").replace("\\)", ")")
title = title_full[:70].rstrip()
desc_text = (
    f"{title_full[:200]}. "
    f"Estado: {'como nuevo' if props.get('Status') == 'as_good_as_new' else 'usado'}. "
    "Funciona perfectamente."
)[:800]
price_val = str(int(props["Selling Price"]))

cmd_id = 0

async def cdp_eval(ws, expression):
    global cmd_id
    cmd_id += 1
    await ws.send(json.dumps({
        "id": cmd_id,
        "method": "Runtime.evaluate",
        "params": {"expression": expression, "returnByValue": True}
    }))
    while True:
        msg = json.loads(await ws.recv())
        if msg.get("id") == cmd_id:
            return msg.get("result", {}).get("result", {}).get("value")

async def fill_form():
    ws_url = get_form_tab_ws()
    if not ws_url:
        print("ERROR: Milanuncios form tab not found")
        sys.exit(1)
    print(f"Connecting: {ws_url}")
    
    async with websockets.connect(ws_url, max_size=10_000_000) as ws:
        # Check title
        title_val = json.dumps(title)
        desc_val = json.dumps(desc_text)
        price_str = json.dumps(price_val)
        
        r = await cdp_eval(ws, "document.title")
        print(f"Page: {r}")
        
        # Fill title
        js = f"""(function() {{
  var el = document.querySelector("input[placeholder*='vendes']") || 
           document.querySelector("input[placeholder*='Titulo']");
  if (!el) return "NOT FOUND";
  var setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
  setter.call(el, {title_val});
  el.dispatchEvent(new Event('input', {{bubbles:true}}));
  el.dispatchEvent(new Event('change', {{bubbles:true}}));
  return "OK:" + el.value.substring(0,40);
}})()"""
        r = await cdp_eval(ws, js)
        print(f"Title: {r}")
        await asyncio.sleep(0.5)
        
        # Fill desc
        js = f"""(function() {{
  var el = document.querySelector("textarea");
  if (!el) return "NOT FOUND";
  var setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
  setter.call(el, {desc_val});
  el.dispatchEvent(new Event('input', {{bubbles:true}}));
  el.dispatchEvent(new Event('change', {{bubbles:true}}));
  return "OK:" + el.value.substring(0,40);
}})()"""
        r = await cdp_eval(ws, js)
        print(f"Desc: {r}")
        await asyncio.sleep(0.5)
        
        # Fill price
        js = f"""(function() {{
  var el = document.querySelector("input[type='number']");
  if (!el) return "NOT FOUND";
  var setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
  setter.call(el, {price_str});
  el.dispatchEvent(new Event('input', {{bubbles:true}}));
  el.dispatchEvent(new Event('change', {{bubbles:true}}));
  return "OK:" + el.value;
}})()"""
        r = await cdp_eval(ws, js)
        print(f"Price: {r}")
        await asyncio.sleep(0.5)
        
        # Click condition dropdown
        js = """(function() {
  var inputs = Array.from(document.querySelectorAll("input"));
  var condInput = inputs.find(i => i.placeholder && i.placeholder.toLowerCase().includes('estado'));
  if (!condInput) {
    // Try to find by nearby label
    var allDivs = Array.from(document.querySelectorAll("div, span, label"));
    var label = allDivs.find(d => d.textContent.trim() === 'Estado del producto');
    if (label) {
      var inp = label.closest('[class]').querySelector('input');
      if (inp) condInput = inp;
    }
  }
  if (!condInput) return "NOT FOUND";
  condInput.click();
  return "CLICKED:" + condInput.placeholder;
})()"""
        r = await cdp_eval(ws, js)
        print(f"Condition click: {r}")
        await asyncio.sleep(1)
        
        # Select "como nuevo"
        js = """(function() {
  var opts = Array.from(document.querySelectorAll("li[role='option'], div[role='option'], ul li, li"));
  var all = opts.map(o => o.textContent.trim().substring(0,25)).filter(t => t.length > 0);
  var opt = opts.find(o => {
    var t = o.textContent.trim().toLowerCase();
    return t.includes('nuevo') || t === 'como nuevo' || t.includes('como nuevo');
  });
  if (!opt) return "NOT FOUND, options: " + all.slice(0,8).join("|");
  opt.click();
  return "SELECTED: " + opt.textContent.trim();
})()"""
        r = await cdp_eval(ws, js)
        print(f"Condition select: {r}")
        await asyncio.sleep(0.5)
        
        # Now click "No hago envios"
        js = """(function() {
  var btns = Array.from(document.querySelectorAll("div, span, label, li, button"));
  var btn = btns.find(b => b.textContent.trim().toLowerCase().includes('no hago env'));
  if (btn) { btn.click(); return "NO ENVIO CLICKED"; }
  return "no envio btn not found";
})()"""
        r = await cdp_eval(ws, js)
        print(f"No envio: {r}")
        await asyncio.sleep(0.5)
        
        print("FORM_FILLED")

asyncio.run(fill_form())
