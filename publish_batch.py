#!/usr/bin/env python3
"""Publish multiple products from Notion to Milanuncios"""
import subprocess, sys, os, time, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COUNT = 5
DELAY = 50  # seconds between publications

for i in range(COUNT):
    print(f"\n{'='*50}")
    print(f"PUBLICATION {i+1}/{COUNT}")
    print('='*50)
    
    # Fetch next product
    result = subprocess.run(
        [sys.executable, 'fetch_product_for_milanuncios.py'],
        capture_output=True, text=True, cwd=SCRIPT_DIR, encoding='utf-8', errors='replace'
    )
    out = result.stdout.strip()
    print("Fetch:", out[:100])
    
    if not out.startswith('OK'):
        print("No more products or error. Stopping.")
        break
    
    # Publish
    result = subprocess.run(
        [sys.executable, 'publish_one.py'],
        capture_output=True, text=True, cwd=SCRIPT_DIR, encoding='utf-8', errors='replace'
    )
    print(result.stdout.strip()[-300:])
    if result.returncode != 0:
        print("ERROR:", result.stderr.strip()[-100:])
    
    if i < COUNT - 1:
        print(f"\nWaiting {DELAY}s before next publication...")
        time.sleep(DELAY)

print("\nBatch complete!")
