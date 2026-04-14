#!/usr/bin/env python3
"""
Milanuncios Photo Upload - Complete Workflow
Uses OpenClaw browser tool (not Selenium!)

This script automates:
1. Open form
2. Find file input
3. Upload photo file
4. Click "Subir fotos" button
5. Wait for upload completion

Requirements: OpenClaw browser must be connected (profile="openclaw" or profile="chrome")
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime

# Constants
FORM_URL = 'https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447'
PHOTO_PATH = r'C:\Users\Val\.openclaw\workspace\milanuncios-poster\temp\test_photo.jpg'
UPLOAD_BUTTON_SELECTOR = '#modal-react-portal > div.sui-MoleculeModal.is-MoleculeModal-open > div > footer > div > button'

def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {msg}")

def find_file_input_selector():
    """JavaScript to find the file input selector"""
    return """
    const inputs = document.querySelectorAll('input[type="file"]');
    if (inputs.length === 0) {
        return { error: 'No file inputs found' };
    }
    
    let photoInput = null;
    for (let i = 0; i < inputs.length; i++) {
        const inp = inputs[i];
        if (inp.accept.includes('image') || inp.id.includes('photo') || inp.name.includes('photo')) {
            photoInput = inp;
            break;
        }
    }
    
    if (!photoInput) photoInput = inputs[0];
    
    return {
        found: true,
        id: photoInput.id,
        name: photoInput.name,
        selector: photoInput.id ? '#' + photoInput.id : 'input[type="file"]'
    };
    """

def get_file_input_ref():
    """Get reference to file input for browser.act()"""
    return """
    const inputs = document.querySelectorAll('input[type="file"]');
    // Return the element ref that browser.act() can use
    return inputs.length > 0 ? inputs[0] : null;
    """

def main_workflow():
    """
    Main workflow - shows what to run in browser tool
    """
    
    log("=" * 70)
    log("MILANUNCIOS PHOTO UPLOAD - WORKFLOW")
    log("=" * 70)
    print()
    
    if not os.path.exists(PHOTO_PATH):
        log(f"Photo not found: {PHOTO_PATH}", "ERROR")
        return False
    
    log(f"Photo path: {PHOTO_PATH}")
    print()
    
    log("STEP-BY-STEP COMMANDS FOR BROWSER TOOL")
    log("=" * 70)
    print()
    
    # Step 1
    print("""
[STEP 1] Open Milanuncios form
─────────────────────────────────────────────────────────────────────

CODE:
    from browser import action
    await action({
        'action': 'open',
        'profile': 'openclaw',
        'targetUrl': 'https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447',
        'timeoutMs': 20000
    })

Wait for page to load...
    """)
    
    # Step 2
    print("""
[STEP 2] Take screenshot to see current state
─────────────────────────────────────────────────────────────────────

CODE:
    from browser import action
    await action({
        'action': 'screenshot',
        'targetId': 'BROWSER_TAB_ID'  # from previous step
    })

This shows the form and where the upload button is
    """)
    
    # Step 3
    print("""
[STEP 3] Find file input element
─────────────────────────────────────────────────────────────────────

CODE:
    from browser import action
    result = await action({
        'action': 'act',
        'targetId': 'BROWSER_TAB_ID',
        'request': {
            'kind': 'evaluate',
            'fn': '''
const inputs = document.querySelectorAll('input[type="file"]');
console.log('[UPLOAD] Found ' + inputs.length + ' file inputs');
inputs.forEach((inp, i) => {
    console.log('[INPUT ' + i + '] id=' + inp.id + ', name=' + inp.name);
});
return { count: inputs.length, firstId: inputs[0]?.id };
            '''
        }
    })

Result will show the file input ID/selector
    """)
    
    # Step 4
    print("""
[STEP 4] Upload photo file
─────────────────────────────────────────────────────────────────────

Once you know the input selector (e.g., 'input[type="file"]' or '#photoInput'):

CODE:
    from browser import action
    await action({
        'action': 'act',
        'targetId': 'BROWSER_TAB_ID',
        'request': {
            'kind': 'type',
            'selector': 'input[type="file"]',  # or the specific selector you found
            'text': r'C:\\Users\\Val\\.openclaw\\workspace\\milanuncios-poster\\temp\\test_photo.jpg'
        }
    })

This selects the photo file and triggers the upload modal
    """)
    
    # Step 5
    print("""
[STEP 5] Wait for modal to appear
─────────────────────────────────────────────────────────────────────

Wait 2-3 seconds for the "Subir fotos" modal to appear

In browser console you can check:
    document.querySelector('#modal-react-portal')  // Should exist now
    """)
    
    # Step 6
    print("""
[STEP 6] Click "Subir fotos" button
─────────────────────────────────────────────────────────────────────

CODE:
    from browser import action
    await action({
        'action': 'act',
        'targetId': 'BROWSER_TAB_ID',
        'request': {
            'kind': 'click',
            'selector': '#modal-react-portal > div.sui-MoleculeModal.is-MoleculeModal-open > div > footer > div > button'
        }
    })

This clicks the upload button and starts the upload
    """)
    
    # Step 7
    print("""
[STEP 7] Wait and verify
─────────────────────────────────────────────────────────────────────

Wait 3-5 seconds for upload to complete

Check if:
- Modal closes
- Photo appears in form
- No error messages

Take screenshot to verify:
    await action({
        'action': 'screenshot',
        'targetId': 'BROWSER_TAB_ID'
    })
    """)
    
    print()
    log("=" * 70)
    print()
    
    # Alternative: Simpler selector approach
    print("""
[ALTERNATIVE] If button selector doesn't work, try:
─────────────────────────────────────────────────────────────────────

// Find all buttons and click the one with "Subir" text
const buttons = document.querySelectorAll('button');
for (let btn of buttons) {
    if (btn.textContent.includes('Subir')) {
        btn.click();
        break;
    }
}
    """)
    
    print()
    log("=" * 70)
    
    # Save to file
    save_instructions(PHOTO_PATH)
    
    return True

def save_instructions(photo_path):
    """Save all instructions to a file"""
    
    output_file = Path(__file__).parent / 'PHOTO_UPLOAD_COMPLETE_GUIDE.txt'
    
    content = f"""
MILANUNCIOS PHOTO UPLOAD - COMPLETE GUIDE
Generated: {datetime.now().isoformat()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHOTO FILE TO UPLOAD:
{photo_path}

UPLOAD BUTTON SELECTOR:
#modal-react-portal > div.sui-MoleculeModal.is-MoleculeModal-open > div > footer > div > button

FORM URL:
https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUICK START:

1. Open form in browser
2. Find file input with: document.querySelectorAll('input[type="file"]')[0]
3. Send photo path to input
4. Click "Subir fotos" button when modal appears
5. Wait for upload to complete

Key insight: Use browser.act() with 'type' kind to send file path,
NOT drag-and-drop or Selenium methods (those get detected).

The modal will appear automatically when file is selected.
The button text is "Subir fotos" (Upload photos).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    log(f"Instructions saved: {output_file}")

if __name__ == '__main__':
    main_workflow()
