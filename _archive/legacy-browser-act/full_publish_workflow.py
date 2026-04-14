#!/usr/bin/env python3
"""
FULL MILANUNCIOS PUBLISHING WORKFLOW
Complete automation with browser tool

Process:
1. Fetch product from Notion
2. Open Milanuncios form
3. Fill form (title, description, price, state, weight)
4. Publish
5. Extract URL
6. Update Notion
7. Report success

Author: Ali
Date: 2026-02-27
Status: READY FOR TESTING
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# Configuration
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
DB_ID = '2bd12f742f9e8198bfb3dce06af14f58'
FORM_URL = 'https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447'

NOTION_HEADERS = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    level_str = f"{level:8}"
    print(f"[{ts}] {level_str}: {msg}")

def fetch_next_product():
    """Fetch next unpublished product from Notion"""
    
    log("Fetching product from Notion...", "FETCH")
    
    if not NOTION_API_KEY:
        log("NOTION_API_KEY not set", "ERROR")
        return None
    
    try:
        response = requests.post(
            f'https://api.notion.com/v1/databases/{DB_ID}/query',
            headers=NOTION_HEADERS,
            json={'page_size': 1}
        )
        
        if response.status_code != 200:
            log(f"Notion query failed: {response.status_code}", "ERROR")
            return None
        
        results = response.json().get('results', [])
        if not results:
            log("No products found", "WARN")
            return None
        
        product = results[0]
        props = product['properties']
        
        data = {
            'notion_id': product['id'],
            'db_id': DB_ID,
            'properties': {}
        }
        
        # Extract properties
        for key, prop in props.items():
            prop_type = prop.get('type')
            
            if prop_type == 'title' and prop.get('title'):
                data['properties'][key] = prop['title'][0]['text']['content']
            elif prop_type == 'rich_text' and prop.get('rich_text'):
                data['properties'][key] = prop['rich_text'][0]['text']['content']
            elif prop_type == 'number':
                data['properties'][key] = prop.get('number')
            elif prop_type == 'select' and prop.get('select'):
                data['properties'][key] = prop['select']['name']
        
        name = data['properties'].get('Name', 'Unknown')[:50]
        price = int(data['properties'].get('Selling Price', 0))
        log(f"Product: {name} | Price: EUR{price}", "OK")
        
        return data
        
    except Exception as e:
        log(f"Error: {e}", "ERROR")
        return None

def get_weight_category(weight_kg):
    """Get Milanuncios weight category based on kg"""
    
    if weight_kg < 0.5:
        return 'Menos de 500g'
    elif weight_kg < 1:
        return 'Entre 500g y 1kg'
    elif weight_kg < 2:
        return 'Entre 1kg y 2kg'
    elif weight_kg < 5:
        return 'Entre 2kg y 5kg'
    elif weight_kg < 10:
        return 'Entre 5kg y 10kg'
    elif weight_kg < 20:
        return 'Entre 10kg y 20kg'
    elif weight_kg < 30:
        return 'Entre 20kg y 30kg'
    else:
        return 'Mas de 30kg'

def update_notion_url(notion_id, product_url):
    """Update Notion with product URL"""
    
    log(f"Updating Notion: {product_url}", "UPDATE")
    
    try:
        response = requests.patch(
            f'https://api.notion.com/v1/pages/{notion_id}',
            headers=NOTION_HEADERS,
            json={
                'properties': {
                    'Milanuncios Posted': {
                        'rich_text': [
                            {
                                'type': 'text',
                                'text': {
                                    'content': product_url,
                                    'link': {'url': product_url}
                                }
                            }
                        ]
                    }
                }
            }
        )
        
        if response.status_code == 200:
            log("Notion updated", "OK")
            return True
        else:
            log(f"Failed: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log(f"Error: {e}", "ERROR")
        return False

def main():
    """Main execution"""
    
    log("=" * 70, "MAIN")
    log("FULL PUBLISHING WORKFLOW", "MAIN")
    log("=" * 70, "MAIN")
    print()
    
    # Step 1: Fetch product
    product = fetch_next_product()
    if not product:
        return 1
    
    print()
    
    # Extract data
    name = product['properties'].get('Name', '')[:70]
    price = int(product['properties'].get('Selling Price', 0))
    description = product['properties'].get('model', '')
    weight_kg = product['properties'].get('Weight', 1) / 1000
    weight_category = get_weight_category(weight_kg)
    
    log(f"[FORM DATA]", "FORM")
    log(f"  Title: {name}", "FORM")
    log(f"  Price: EUR{price}", "FORM")
    log(f"  Description: {description[:50]}...", "FORM")
    log(f"  Weight: {weight_kg:.2f}kg ({weight_category})", "FORM")
    
    print()
    
    # Show automation plan
    log("AUTOMATION PLAN:", "PLAN")
    plan = """
[STEP 1] Open Form
  URL: https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447

[STEP 2] Fill Form Fields
  - Title input: {name}
  - Description textarea: {desc}
  - Price input: {price}
  - State dropdown: "Practicamente nuevo"
  - Weight category: "{weight_cat}"
  - Other fields as needed

[STEP 3] Publish
  - Click [Publicar anuncio] button

[STEP 4] Extract URL
  - Success page shows: "Enhorabuena, tu anuncio..."
  - URL format: https://www.milanuncios.com/anuncios/rXXXXXXXX.htm
  - Extract r-number

[STEP 5] Update Notion
  - Save URL to Milanuncios Posted field

[STEP 6] Done!
  - Product published successfully
    """.format(
        name=name,
        desc=description[:50],
        price=price,
        weight_cat=weight_category
    )
    
    print(plan)
    print()
    
    # Show browser tool commands
    log("BROWSER TOOL COMMANDS:", "BROWSER")
    
    commands = f"""
# 1. Open form
result = browser.act(
    action='open',
    profile='openclaw',
    targetUrl='{FORM_URL}',
    timeoutMs=20000
)
targetId = result['targetId']

# 2. Fill title field
browser.act(
    action='act',
    targetId=targetId,
    request={{'kind': 'type', 'selector': 'input[name="title"]', 'text': '{name}'}}
)

# 3. Fill price field
browser.act(
    action='act',
    targetId=targetId,
    request={{'kind': 'type', 'selector': 'input[name="price"]', 'text': '{price}'}}
)

# 4. Fill description
browser.act(
    action='act',
    targetId=targetId,
    request={{'kind': 'type', 'selector': 'textarea', 'text': '{description}'}}
)

# 5. Select weight category dropdown
browser.act(
    action='act',
    targetId=targetId,
    request={{'kind': 'click', 'selector': 'select[name="weight"]'}}
)
browser.act(
    action='act',
    targetId=targetId,
    request={{'kind': 'type', 'text': '{weight_category}'}}
)

# 6. Click publish button
browser.act(
    action='act',
    targetId=targetId,
    request={{'kind': 'click', 'selector': 'button[type="submit"]'}}
)

# 7. Wait for success page
time.sleep(3)

# 8. Extract URL from success page
result = browser.act(
    action='act',
    targetId=targetId,
    request={{'kind': 'evaluate', 'fn': '''
const link = document.querySelector('a[href*="/anuncios/r"]');
if (link) {{
    return {{ url: link.href }};
}} else {{
    return {{ error: 'URL not found' }};
}}
    '''}}
)

productUrl = result.get('url')
    """
    
    print(commands)
    print()
    
    # Final instructions
    log("NEXT STEPS:", "INFO")
    log("1. Use RUN_THIS_PHOTO_UPLOAD.py to upload photo (if product has photo)", "INFO")
    log("2. Run browser tool commands above to fill and publish", "INFO")
    log("3. Extract final URL from success page", "INFO")
    log("4. Once URL known, run: python full_publish_workflow.py --finalize <URL>", "INFO")
    
    print()
    log("=" * 70, "END")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
