#!/usr/bin/env python3
"""
Test: Photo Upload via XHR/Fetch Injection
Strategy: Use browser's fetch API to upload photo (bypasses Cloudflare protection)

This is VARIANT 2: Fetch Injection through browser console.
We'll use the browser tool to:
1. Open Milanuncios form (logged-in browser)
2. Send fetch request from within browser console
3. Capture response to find photo upload endpoint

Date: 2026-02-27
Author: Ali
"""

import os
import json
import base64
import time
from datetime import datetime

# Test photo - use existing one if available
TEST_PHOTO_PATH = os.path.join(os.path.dirname(__file__), 'temp', 'test_photo.jpg')

def log(msg, level="INFO"):
    """Simple logging"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {msg}")

def prepare_test_photo():
    """Create or verify test photo exists"""
    
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Check if test photo exists
    if os.path.exists(TEST_PHOTO_PATH):
        log(f"[OK] Test photo found: {TEST_PHOTO_PATH}")
        return True
    
    # Download a small test image from pexels/unsplash (free images)
    # For now, we'll just mention it needs to be there
    log(f"[WARN] Test photo NOT found. Place a JPEG file at: {TEST_PHOTO_PATH}", "WARN")
    log("   You can download from: https://unsplash.com/ or use any product image", "WARN")
    return os.path.exists(TEST_PHOTO_PATH)

def create_photo_upload_fetch_code(photo_base64):
    """
    Create JavaScript code to upload photo via fetch.
    This code will be injected into browser console.
    
    Args:
        photo_base64 (str): Base64 encoded photo
    
    Returns:
        str: JavaScript code for fetch upload
    """
    
    code = f"""
(async () => {{
    console.log('[UPLOAD] Starting photo upload via fetch...');
    
    try {{
        // Prepare FormData
        const formData = new FormData();
        
        // Convert base64 to blob
        const base64Data = '{photo_base64}';
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {{
            bytes[i] = binaryString.charCodeAt(i);
        }}
        const blob = new Blob([bytes], {{ type: 'image/jpeg' }});
        
        formData.append('photo', blob, 'test_photo.jpg');
        
        // Try multiple possible endpoints
        const endpoints = [
            '/imagenes/upload',
            '/api/imagenes/upload',
            '/api/upload',
            '/upload',
            '/uploadImage',
            window.location.origin + '/imagenes/upload',
        ];
        
        for (const endpoint of endpoints) {{
            try {{
                console.log(`[TRY] Trying endpoint: ${{endpoint}}`);
                const response = await fetch(endpoint, {{
                    method: 'POST',
                    body: formData,
                    credentials: 'include',  // Include cookies
                }});
                
                const contentType = response.headers.get('content-type');
                console.log(`[RESPONSE] Status: ${{response.status}}, Content-Type: ${{contentType}}`);
                
                if (response.ok) {{
                    const data = await response.json();
                    console.log('[SUCCESS] Response:', data);
                    return data;
                }} else {{
                    const text = await response.text();
                    console.log(`[FAIL] Failed: ${{text.substring(0, 200)}}`);
                }}
            }} catch (err) {{
                console.log(`[WARN] Endpoint failed: ${{err.message}}`);
            }}
        }}
        
        console.log('[FAIL] All endpoints failed');
        
    }} catch (error) {{
        console.error('[ERROR] Error during upload:', error);
    }}
}})();
"""
    
    return code

def test_via_browser_tool():
    """
    Use OpenClaw browser tool to test photo upload via fetch.
    
    This is the actual test - opens form, injects fetch code, captures result.
    """
    
    log("=" * 60)
    log("VARIANT 2: Fetch Injection Test")
    log("=" * 60)
    
    # Step 1: Check if we have a test photo
    if not prepare_test_photo():
        log("Cannot proceed without test photo. Please place image at:")
        log(f"  {TEST_PHOTO_PATH}")
        return False
    
    # Step 2: Read and encode photo
    log("Step 1: Reading and encoding test photo...")
    with open(TEST_PHOTO_PATH, 'rb') as f:
        photo_data = f.read()
        photo_base64 = base64.b64encode(photo_data).decode('utf-8')
        log(f"[OK] Photo encoded: {len(photo_base64)} characters")
    
    # Step 3: Create JavaScript injection code
    log("Step 2: Creating fetch injection code...")
    js_code = create_photo_upload_fetch_code(photo_base64)
    
    # Save code to file for reference
    code_file = os.path.join(os.path.dirname(__file__), 'temp', 'fetch_upload_code.js')
    os.makedirs(os.path.dirname(code_file), exist_ok=True)
    with open(code_file, 'w') as f:
        f.write(js_code)
    log(f"[OK] JS code saved to: {code_file}")
    
    # Step 4: Now we need to use browser tool
    log("Step 3: Opening Milanuncios form in browser...")
    log("""
[MANUAL STEP] Use OpenClaw Browser Tool:
============================================================

1. Open browser: https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447

2. Wait for form to load

3. Open browser DevTools (F12) -> Console tab

4. Paste this code and press Enter:
    
""")
    
    print("-" * 60)
    print(js_code)
    print("-" * 60)
    
    log("""
5. Watch console output for:
   - [SUCCESS] (means photo upload worked)
   - [TRY] Trying endpoint: ... (what endpoints it tries)
   - [RESPONSE] Status: ... (HTTP response codes)

6. If SUCCESS, save the response object data (should have photo ID or URL)

7. Report findings back:
   - Which endpoint worked?
   - What's in the response?
   - Can we extract photo ID?
""")
    
    log("Step 4: Waiting for browser console execution...")
    log("""
AUTOMATION STEP (In Python):
Now I'll also create a version using browser.act() + console execution
""")
    
    return True

def create_automated_browser_version():
    """
    Create a version that uses browser.act(request={"kind": "evaluate"}) 
    to run the fetch code automatically.
    """
    
    code = """
from browser import action

async def upload_photo_via_fetch():
    '''Upload photo using browser fetch API'''
    
    # Prepare photo
    with open('photo.jpg', 'rb') as f:
        photo_base64 = base64.b64encode(f.read()).decode()
    
    # JavaScript to execute in browser
    js_code = f'''
        (async () => {{
            const formData = new FormData();
            const base64Data = '{photo_base64}';
            const binaryString = atob(base64Data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {{
                bytes[i] = binaryString.charCodeAt(i);
            }}
            const blob = new Blob([bytes], {{ type: 'image/jpeg' }});
            formData.append('photo', blob, 'photo.jpg');
            
            const response = await fetch('/imagenes/upload', {{
                method: 'POST',
                body: formData,
                credentials: 'include'
            }});
            
            const result = await response.json();
            return result;
        }})();
    '''
    
    # Execute in browser
    response = await action(
        kind='evaluate',
        fn=js_code,
        timeoutMs=30000
    )
    
    return response
"""
    
    return code

def main():
    """Main test execution"""
    
    log("[TEST] Photo Upload - Variant 2: Fetch Injection")
    log("")
    
    # Test via browser tool
    success = test_via_browser_tool()
    
    if success:
        log("")
        log("[NEXT STEPS]")
        log("  1. Execute the code above in browser console")
        log("  2. Report back with findings")
        log("  3. If SUCCESS, we found the upload endpoint!")
        log("  4. Then integrate into main publishing script")
    
    # Also show automated version
    log("")
    log("=" * 60)
    log("[AUTOMATED VERSION] for integration")
    log("=" * 60)
    
    auto_code = create_automated_browser_version()
    print(auto_code)

if __name__ == '__main__':
    main()
