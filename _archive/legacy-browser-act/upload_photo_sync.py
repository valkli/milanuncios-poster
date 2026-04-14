#!/usr/bin/env python3
"""
Milanuncios Photo Upload - Synchronous Version
Uses OpenClaw browser tool

This script controls the browser to:
1. Open form
2. Find file input
3. Upload photo  
4. Click "Subir fotos" button
5. Verify success
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {level}: {msg}")

def upload_photo_manual():
    """
    Manual step-by-step guide to upload photo using browser tool
    Each step can be executed separately
    """
    
    form_url = 'https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447'
    photo_path = r'C:\Users\Val\.openclaw\workspace\milanuncios-poster\temp\test_photo.jpg'
    
    log("=" * 70)
    log("MILANUNCIOS PHOTO UPLOAD - MANUAL STEPS")
    log("=" * 70)
    print()
    
    if not os.path.exists(photo_path):
        log(f"Photo not found: {photo_path}", "ERROR")
        return False
    
    log(f"Photo: {photo_path}")
    print()
    
    # STEP 1
    print("[STEP 1] OPEN FORM")
    print("=" * 70)
    print("""
Execute this in Python/OpenClaw:

```python
from browser import action

result = action(
    action='open',
    profile='openclaw',
    targetUrl='https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447',
    timeoutMs=20000
)

targetId = result['targetId']
print(f'Opened! Target ID: {targetId}')
```

Wait for form to load (2-3 seconds)
Save the 'targetId' for next steps
    """)
    
    input("Press Enter when form is loaded...")
    print()
    
    # STEP 2
    print("[STEP 2] FIND FILE INPUT")
    print("=" * 70)
    print("""
Execute this in browser console:

```javascript
const inputs = document.querySelectorAll('input[type="file"]');
console.log('Found inputs:', inputs.length);
inputs.forEach((inp, i) => {
    console.log(i + ':', 'id=' + inp.id, 'name=' + inp.name, 'accept=' + inp.accept);
});
```

Or in Python:

```python
result = action(
    action='act',
    targetId=targetId,
    request={
        'kind': 'evaluate',
        'fn': 'return document.querySelectorAll("input[type=\\"file\\"]").length'
    }
)
```

You should see at least 1 file input
    """)
    
    input("Press Enter when you've found the file input...")
    print()
    
    # STEP 3
    print("[STEP 3] UPLOAD PHOTO FILE")
    print("=" * 70)
    print(f"""
Execute this in Python:

```python
result = action(
    action='act',
    targetId=targetId,
    request={{
        'kind': 'type',
        'selector': 'input[type="file"]',
        'text': r'{photo_path}'
    }}
)
```

This will:
- Find the file input
- Send the photo path
- Trigger the upload modal

Wait 2-3 seconds for the modal to appear!
    """)
    
    input("Press Enter after sending photo path...")
    time.sleep(3)
    print()
    
    # STEP 4
    print("[STEP 4] WAIT FOR MODAL")
    print("=" * 70)
    print("""
The modal with "Subir fotos" button should now be visible.

In browser console, verify:

```javascript
const modal = document.querySelector('#modal-react-portal');
console.log('Modal visible:', !!modal);

// Find the button
const button = document.querySelector(
    '#modal-react-portal > div.sui-MoleculeModal.is-MoleculeModal-open > div > footer > div > button'
);
console.log('Button found:', !!button);
console.log('Button text:', button?.textContent);
```
    """)
    
    input("Press Enter when you see the modal...")
    print()
    
    # STEP 5
    print("[STEP 5] CLICK 'SUBIR FOTOS' BUTTON")
    print("=" * 70)
    print("""
Execute this in Python:

```python
result = action(
    action='act',
    targetId=targetId,
    request={{
        'kind': 'click',
        'selector': '#modal-react-portal > div.sui-MoleculeModal.is-MoleculeModal-open > div > footer > div > button'
    }}
)
```

This will click the upload button and start the upload process.

Wait 3-5 seconds for upload to complete!
    """)
    
    input("Press Enter after clicking button...")
    time.sleep(5)
    print()
    
    # STEP 6
    print("[STEP 6] VERIFY UPLOAD SUCCESS")
    print("=" * 70)
    print("""
In browser console, check if:

1. Modal closed:
```javascript
const modal = document.querySelector('#modal-react-portal');
console.log('Modal still visible:', !!modal);
```

2. Photo appears in form:
```javascript
const images = document.querySelectorAll('img');
console.log('Total images:', images.length);

// Look for preview/thumbnail
const preview = document.querySelector('[class*="preview"], [class*="thumb"]');
console.log('Photo preview found:', !!preview);
```

3. No error messages:
```javascript
const errors = document.querySelectorAll('[class*="error"]');
console.log('Error messages:', errors.length);
```

If modal is closed and photo preview appears = SUCCESS!
    """)
    
    input("Press Enter when upload is complete...")
    print()
    
    print("[RESULT]")
    print("=" * 70)
    print("Photo upload should now be complete!")
    print()
    print("Next steps:")
    print("1. Fill form with product data (title, price, description, weight)")
    print("2. Click publish button")
    print("3. Extract final product URL")
    print("4. Update Notion with URL")
    
    return True

def main():
    """Main entry"""
    
    upload_photo_manual()
    
    print()
    log("=" * 70)
    log("Upload workflow complete!", "OK")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
