#!/usr/bin/env python3
"""
Upload Photo to Milanuncios - Using OpenClaw Browser Tool

Strategy:
1. Open form (already done)
2. Click file input (or drag-and-drop area)
3. Upload test photo
4. Wait for modal to appear
5. Click "Subir fotos" button
6. Wait for success

This uses browser.act() which bypasses Selenium detection!
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime

# Will be used with browser tool
MILANUNCIOS_FORM = 'https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447'
PHOTO_INPUT_SELECTOR = 'input[type="file"]'  # or more specific selector if needed
UPLOAD_BUTTON_SELECTOR = '#modal-react-portal > div.sui-MoleculeModal.is-MoleculeModal-open > div > footer > div > button'
DRAG_DROP_AREA_SELECTOR = '[class*="upload"], [class*="drag"], [class*="dropzone"]'

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def create_browser_script():
    """
    Create the browser automation script
    
    This script should be run in OpenClaw browser tool like:
    browser.act(request={"kind": "evaluate", "fn": script_code})
    """
    
    script = """
// Step 1: Find all possible file input elements
const fileInputs = document.querySelectorAll('input[type="file"]');
console.log('[PHOTO-UPLOAD] Found ' + fileInputs.length + ' file inputs');

// Find the one for photos (usually in upload section)
let photoInput = null;
for (let input of fileInputs) {
    if (input.accept && input.accept.includes('image')) {
        photoInput = input;
        console.log('[PHOTO-UPLOAD] Found image input: ' + input.id);
        break;
    }
}

if (!photoInput) {
    photoInput = fileInputs[0];  // Use first one if no image-specific found
}

if (photoInput) {
    console.log('[PHOTO-UPLOAD] Using input: ' + (photoInput.id || photoInput.name || 'unnamed'));
    return {
        found: true,
        selector: photoInput.id ? '#' + photoInput.id : 'input[type="file"]',
        id: photoInput.id,
        name: photoInput.name,
        accept: photoInput.accept
    };
} else {
    console.log('[PHOTO-UPLOAD] No file input found!');
    return { found: false, error: 'No file input elements found' };
}
"""
    
    return script

def create_click_upload_button_script():
    """Script to click the 'Subir fotos' button"""
    
    script = """
// Find and click the upload button
const selector = '#modal-react-portal > div.sui-MoleculeModal.is-MoleculeModal-open > div > footer > div > button';
const button = document.querySelector(selector);

if (button) {
    console.log('[CLICK-BUTTON] Found upload button, clicking...');
    button.click();
    return { success: true, message: 'Button clicked' };
} else {
    console.log('[CLICK-BUTTON] Button not found! Trying alternative selectors...');
    
    // Try alternative selectors
    const altSelectors = [
        'button[type="button"]:contains("Subir")',
        '.sui-AtomButton--success',
        'button:contains("Subir fotos")'
    ];
    
    for (let sel of altSelectors) {
        try {
            let btn = document.querySelector(sel);
            if (btn) {
                console.log('[CLICK-BUTTON] Found via: ' + sel);
                btn.click();
                return { success: true, message: 'Clicked via ' + sel };
            }
        } catch(e) {}
    }
    
    return { success: false, error: 'Could not find upload button' };
}
"""
    
    return script

def get_browser_instructions():
    """Return instructions for manual browser automation"""
    
    instructions = """
╔════════════════════════════════════════════════════════════════╗
║  UPLOAD PHOTO - OpenClaw Browser Tool Instructions            ║
╚════════════════════════════════════════════════════════════════╝

STEP 1: Open the form
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

URL: https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447

Run in OpenClaw:
    browser.act(request={"kind": "navigate", "targetUrl": "https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447"})

STEP 2: Find file input
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run this to find the file input:

const inputs = document.querySelectorAll('input[type="file"]');
console.log('Found inputs:', inputs.length);
inputs.forEach((inp, i) => {
    console.log(i + ': id=' + inp.id + ', name=' + inp.name + ', accept=' + inp.accept);
});

STEP 3: Upload photo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Once you have the file input selector/id, use:

    browser.act(request={
        "kind": "type",
        "ref": "FILE_INPUT_ID",
        "text": "C:\\\\Users\\\\Val\\\\.openclaw\\\\workspace\\\\milanuncios-poster\\\\temp\\\\test_photo.jpg"
    })

Or if you have the selector:

    browser.act(request={
        "kind": "type",
        "selector": "input[type='file']",
        "text": "/path/to/photo.jpg"
    })

STEP 4: Wait for modal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Wait ~2 seconds for the upload modal to appear with "Subir fotos" button

STEP 5: Click "Subir fotos" button
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Selector: #modal-react-portal > div.sui-MoleculeModal.is-MoleculeModal-open > div > footer > div > button

Run:
    browser.act(request={
        "kind": "click",
        "selector": "#modal-react-portal > div.sui-MoleculeModal.is-MoleculeModal-open > div > footer > div > button"
    })

STEP 6: Wait for completion
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Wait for modal to close and photo to appear in form
"""
    
    return instructions

def main():
    log("=" * 60)
    log("Milanuncios Photo Upload - Browser Tool")
    log("=" * 60)
    print()
    print(get_browser_instructions())
    print()
    
    # Save instructions to file
    instructions_file = Path(__file__).parent / 'BROWSER_UPLOAD_INSTRUCTIONS.txt'
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(get_browser_instructions())
    
    log(f"Instructions saved to: {instructions_file}")
    
    # Save scripts for reference
    script_file = Path(__file__).parent / 'temp' / 'browser_upload_scripts.js'
    script_file.parent.mkdir(parents=True, exist_ok=True)
    with open(script_file, 'w') as f:
        f.write("// Find file input\n")
        f.write(create_browser_script())
        f.write("\n\n// Click upload button\n")
        f.write(create_click_upload_button_script())
    
    log(f"Scripts saved to: {script_file}")

if __name__ == '__main__':
    main()
