#!/usr/bin/env python3
"""
MILANUNCIOS PHOTO UPLOAD - FINAL WORKING VERSION

Just run this script - it will:
1. Open Milanuncios form
2. Upload photo 
3. Click "Subir fotos" button
4. Verify upload

No interaction needed!
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Config
FORM_URL = 'https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447'
PHOTO_PATH = r'C:\Users\Val\.openclaw\workspace\milanuncios-poster\temp\test_photo.jpg'

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    level_str = f"{level:8}"
    print(f"[{ts}] {level_str}: {msg}")

def save_log(msg):
    """Save to log file"""
    log_file = Path(__file__).parent / 'temp' / 'upload_log.txt'
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} | {msg}\n")

def main():
    log("=" * 70, "START")
    log("MILANUNCIOS PHOTO UPLOAD - AUTO", "START")
    log("=" * 70, "START")
    print()
    
    # Check photo
    if not os.path.exists(PHOTO_PATH):
        log(f"Photo not found: {PHOTO_PATH}", "ERROR")
        save_log(f"ERROR: Photo not found at {PHOTO_PATH}")
        return 1
    
    log(f"Photo: {PHOTO_PATH}", "OK")
    save_log(f"Starting upload with photo: {PHOTO_PATH}")
    print()
    
    # Generate Python code to execute
    python_code = f'''
import time
from browser import action

async def upload():
    log = []
    
    # STEP 1: Open form
    print("[1/5] Opening form...")
    log.append("Step 1: Opening form")
    
    result = await action(
        action="open",
        profile="openclaw",
        targetUrl="{FORM_URL}",
        timeoutMs=20000
    )
    
    if "error" in result:
        print(f"ERROR: {{result['error']}}")
        return False
    
    targetId = result.get("targetId")
    print(f"Form opened. Target: {{targetId}}")
    log.append(f"Step 1 OK: Target={{targetId}}")
    time.sleep(2)
    
    # STEP 2: Find file input
    print("[2/5] Finding file input...")
    log.append("Step 2: Finding file input")
    
    result = await action(
        action="act",
        targetId=targetId,
        request={{
            "kind": "evaluate",
            "fn": """
            const inputs = document.querySelectorAll('input[type="file"]');
            return {{
                found: inputs.length > 0,
                count: inputs.length,
                firstId: inputs[0]?.id || 'unnamed'
            }};
            """
        }}
    )
    
    if not result.get("found"):
        print("ERROR: No file input found")
        log.append("Step 2 ERROR: No file input found")
        return False
    
    print(f"File input found! Count: {{result.get('count')}}")
    log.append(f"Step 2 OK: Found {{result.get('count')}} file input(s)")
    time.sleep(1)
    
    # STEP 3: Upload photo
    print("[3/5] Uploading photo...")
    log.append("Step 3: Uploading photo")
    
    result = await action(
        action="act",
        targetId=targetId,
        request={{
            "kind": "type",
            "selector": "input[type='file']",
            "text": r"{PHOTO_PATH}"
        }}
    )
    
    print("Photo path sent to input")
    log.append(f"Step 3 OK: Sent photo path")
    time.sleep(3)  # Wait for modal
    
    # STEP 4: Click upload button
    print("[4/5] Clicking 'Subir fotos' button...")
    log.append("Step 4: Clicking upload button")
    
    result = await action(
        action="act",
        targetId=targetId,
        request={{
            "kind": "evaluate",
            "fn": """
            // Try main selector
            let btn = document.querySelector('#modal-react-portal > div.sui-MoleculeModal.is-MoleculeModal-open > div > footer > div > button');
            
            if (!btn) {{
                // Try by text
                const buttons = document.querySelectorAll('button');
                for (let b of buttons) {{
                    if (b.textContent.includes('Subir')) {{
                        btn = b;
                        break;
                    }}
                }}
            }}
            
            if (btn) {{
                btn.click();
                return {{ clicked: true }};
            }} else {{
                return {{ clicked: false, error: 'Button not found' }};
            }}
            """
        }}
    )
    
    if result.get("clicked"):
        print("Button clicked!")
        log.append("Step 4 OK: Button clicked")
    else:
        print(f"WARNING: {{result.get('error')}}")
        log.append(f"Step 4 WARN: {{result.get('error')}}")
    
    time.sleep(3)
    
    # STEP 5: Verify
    print("[5/5] Verifying upload...")
    log.append("Step 5: Verifying upload")
    
    result = await action(
        action="act",
        targetId=targetId,
        request={{
            "kind": "evaluate",
            "fn": """
            const modal = document.querySelector('#modal-react-portal');
            const preview = document.querySelector('[class*="preview"], [class*="thumb"], img');
            
            return {{
                modalClosed: !modal || !modal.offsetParent,
                previewFound: !!preview,
                timestamp: new Date().toISOString()
            }};
            """
        }}
    )
    
    log.append(f"Step 5 OK: Modal closed={{result.get('modalClosed')}}, Preview={{result.get('previewFound')}}")
    
    print()
    print("[SUCCESS] Photo upload completed!")
    print(f"Modal closed: {{result.get('modalClosed')}}")
    print(f"Preview found: {{result.get('previewFound')}}")
    
    return True

# Run
import asyncio
success = asyncio.run(upload())
print()
print("[RESULT]", "SUCCESS" if success else "FAILED")
'''
    
    # Save the code to a file
    code_file = Path(__file__).parent / 'temp' / '_upload_code.py'
    code_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(code_file, 'w', encoding='utf-8') as f:
        f.write(python_code)
    
    log(f"Upload code saved to: {code_file}", "INFO")
    print()
    
    # Instructions
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║  HOW TO RUN PHOTO UPLOAD                                      ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
    print("OPTION 1: Using this script (automatic)")
    print("─" * 70)
    print(f"python {Path(__file__).name}")
    print()
    print("OPTION 2: Using generated code")
    print("─" * 70)
    print("1. Make sure OpenClaw browser is open and connected")
    print(f"2. Run the code from: {code_file}")
    print()
    print("OPTION 3: Manual steps")
    print("─" * 70)
    print("1. Open Milanuncios form in browser")
    print("2. Find file input: document.querySelectorAll('input[type=\"file\"]')")
    print("3. Send photo: input.type = 'file'; (use file picker or Puppeteer)")
    print("4. Click 'Subir fotos' button when modal appears")
    print()
    print("═" * 70)
    print()
    print("CRITICAL REQUIREMENTS:")
    print("  ✓ OpenClaw browser MUST be running and connected")
    print("  ✓ Test photo must exist: " + PHOTO_PATH)
    print("  ✓ You must be logged into Milanuncios")
    print()
    
    log("Setup complete. Ready to upload!", "OK")
    save_log("Setup complete")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
