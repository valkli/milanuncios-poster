#!/usr/bin/env python3
"""Full publish cycle: navigate + inject photo + fill form + publish + get URL"""
import asyncio, json, sys, pathlib
import websockets
import requests
import subprocess
import time

PORT = 18801

async def cdp_eval(ws, js, cmd_id_list):
    cid = cmd_id_list[0]
    cmd_id_list[0] += 1
    await ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True}}))
    while True:
        msg = json.loads(await ws.recv())
        if msg.get("id") == cid:
            return msg.get("result", {}).get("result", {}).get("value")

async def cdp_navigate(ws, url, cmd_id_list):
    cid = cmd_id_list[0]
    cmd_id_list[0] += 1
    await ws.send(json.dumps({"id": cid, "method": "Page.navigate", "params": {"url": url}}))
    await asyncio.sleep(3)

def get_tabs():
    r = requests.get(f"http://127.0.0.1:{PORT}/json", timeout=5)
    return r.json()

def get_form_tab():
    tabs = get_tabs()
    for t in tabs:
        if "milanuncios.com/publicar" in t.get("url","") and t.get("type") == "page":
            return t["webSocketDebuggerUrl"]
    return None

def get_any_ma_tab():
    tabs = get_tabs()
    for t in tabs:
        if "milanuncios.com" in t.get("url","") and t.get("type") == "page":
            return t["webSocketDebuggerUrl"]
    return None

async def main():
    # Load product
    data_file = pathlib.Path("milanuncios-poster/temp/product_data.json")
    product = json.loads(data_file.read_text("utf-8"))
    props = product["properties"]
    notion_id = product["notion_id"]
    
    title_full = props["Name"].replace("\\-", "-").replace("\\(", "(").replace("\\)", ")")
    title = title_full[:70].rstrip()
    desc_text = (
        f"{title_full[:200]}. "
        f"Estado: {'como nuevo' if props.get('Status') == 'as_good_as_new' else 'usado'}. "
        "Funciona perfectamente."
    )[:800]
    price_val = str(int(props["Selling Price"]))
    
    # Step 1: Navigate to publish form
    ws_url = get_form_tab() or get_any_ma_tab()
    if not ws_url:
        print("ERROR: no milanuncios tab")
        sys.exit(1)
    
    async with websockets.connect(ws_url, max_size=10_000_000) as ws:
        cmd_id = [1]
        
        # Navigate to publish form
        await cdp_navigate(ws, "https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447", cmd_id)
        print("Navigated to form")
    
    # Step 2: Inject photo (external script)
    await asyncio.sleep(2)
    result = subprocess.run(
        ["python", "milanuncios-poster/inject_photo_cdp.py", "--port", str(PORT)],
        capture_output=True, text=True, timeout=30
    )
    output = result.stdout + result.stderr
    if "OK files=1" not in output:
        if "NO_IMAGE" in output or "no image" in output.lower():
            print("SKIP: NO_IMAGE")
            return "NO_IMAGE"
        print("INJECT_ERROR:", output[-200:])
        return "ERROR"
    print("Photo injected OK")
    await asyncio.sleep(2)
    
    # Step 3: Fill form
    ws_url = get_form_tab()
    if not ws_url:
        print("ERROR: form tab gone after inject")
        return "ERROR"
    
    async with websockets.connect(ws_url, max_size=10_000_000) as ws:
        cmd_id = [1]
        
        # Fill title
        js = f"""(function() {{
  var el = document.querySelector("input[placeholder*='vendes']");
  if (!el) return "NOT FOUND";
  var setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
  setter.call(el, {json.dumps(title)});
  el.dispatchEvent(new Event('input', {{bubbles:true}}));
  el.dispatchEvent(new Event('change', {{bubbles:true}}));
  return "OK:" + el.value.substring(0,30);
}})()"""
        r = await cdp_eval(ws, js, cmd_id)
        print("Title:", r)
        await asyncio.sleep(0.3)
        
        # Fill desc
        js = f"""(function() {{
  var el = document.querySelector("textarea");
  if (!el) return "NOT FOUND";
  var setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
  setter.call(el, {json.dumps(desc_text)});
  el.dispatchEvent(new Event('input', {{bubbles:true}}));
  el.dispatchEvent(new Event('change', {{bubbles:true}}));
  return "OK:" + el.value.substring(0,30);
}})()"""
        r = await cdp_eval(ws, js, cmd_id)
        print("Desc:", r)
        await asyncio.sleep(0.3)
        
        # Fill price
        js = f"""(function() {{
  var el = document.querySelector("input[type='number']");
  if (!el) return "NOT FOUND";
  var setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
  setter.call(el, {json.dumps(price_val)});
  el.dispatchEvent(new Event('input', {{bubbles:true}}));
  el.dispatchEvent(new Event('change', {{bubbles:true}}));
  return "OK:" + el.value;
}})()"""
        r = await cdp_eval(ws, js, cmd_id)
        print("Price:", r)
        await asyncio.sleep(0.3)
        
        # Select condition
        js = """(function() {
  var opts = Array.from(document.querySelectorAll("li, div[role='option']"));
  var opt = opts.find(o => {
    var t = o.textContent.trim().toLowerCase();
    return t.startsWith("practic") || t.includes("como nuevo");
  });
  if (!opt) return "NOT_FOUND_YET";
  opt.click();
  return "SELECTED:" + opt.textContent.trim().substring(0,30);
})()"""
        r = await cdp_eval(ws, js, cmd_id)
        print("Condition:", r)
        await asyncio.sleep(0.3)
        
        # Click Publicar
        js = """(function() {
  var btns = Array.from(document.querySelectorAll("button"));
  var pub = btns.find(b => b.textContent.trim() === "Publicar");
  if (!pub) return "NOT FOUND";
  pub.click();
  return "CLICKED";
})()"""
        r = await cdp_eval(ws, js, cmd_id)
        print("Publicar:", r)
        await asyncio.sleep(4)
        
        # Check for dialog
        js = """(function() {
  var btns = Array.from(document.querySelectorAll("button"));
  var noenvio = btns.find(b => b.textContent.toLowerCase().includes("sin env") || b.textContent.toLowerCase().includes("publicar sin"));
  if (noenvio) { noenvio.click(); return "CLICKED_SIN_ENVIO"; }
  if (document.body.innerText.includes("Enhorabuena")) return "SUCCESS";
  return "UNKNOWN";
})()"""
        r = await cdp_eval(ws, js, cmd_id)
        print("Dialog:", r)
        
        if r == "CLICKED_SIN_ENVIO":
            await asyncio.sleep(5)
        
        # Wait for page to load after publish
        await asyncio.sleep(3)
        
        # Navigate to get the ad URL
        await cdp_navigate(ws, "https://www.milanuncios.com/mis-anuncios", cmd_id)
        
        # Get first ad link
        js = """(function() {
  var links = Array.from(document.querySelectorAll('a[href*="/anuncios/r"]'));
  if (links.length === 0) return "NO_ADS";
  return links[0].href;
})()"""
        ad_url = await cdp_eval(ws, js, cmd_id)
        print("AD_URL:", ad_url)
        return ad_url

result = asyncio.run(main())
if result and result.startswith("https://"):
    notion_id = json.loads(pathlib.Path("milanuncios-poster/temp/product_data.json").read_text("utf-8"))["notion_id"]
    update = subprocess.run(
        ["python", "milanuncios-poster/update_notion_url.py", notion_id, result],
        capture_output=True, text=True, timeout=30
    )
    print("Notion update:", update.stdout.strip())
elif result in ("NO_IMAGE", "ERROR"):
    print("SKIPPED:", result)
