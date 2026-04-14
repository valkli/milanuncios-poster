# Milanuncios Auto-Publisher

> Autonomous listing publisher for Milanuncios.com — Spain's largest classifieds platform.

## Overview

An AI-powered agent skill that fetches products from a Notion inventory database and automatically publishes listings on Milanuncios, including photo upload, form completion, and post-publish tracking.

## Features

- **Notion integration** — pulls unpublished products directly from inventory database
- **Automated form filling** — title, description, price, condition, weight
- **Photo injection via CDP** — uploads product images using Chrome DevTools Protocol, bypassing CORS restrictions
- **Post-publish URL capture** — extracts listing URL and writes it back to Notion
- **Anti-spam compliance** — configurable delays between publications
- **Zello notifications** — voice notification after each successful publish

## Architecture

```
Notion DB → fetch_product_for_milanuncios.py
          → Browser (OpenClaw profile)
          → inject_photo_cdp.py (CDP WebSocket photo upload)
          → milanuncios.com/publicar
          → update_notion_url.py → Notion DB
```

## Requirements

- Python 3.10+
- Notion API Key (`NOTION_API_KEY` env variable)
- OpenClaw browser profile (pre-authenticated session)
- Chrome DevTools Protocol (CDP) enabled on port 18800

## Usage

```bash
# Fetch next product from Notion
python fetch_product_for_milanuncios.py

# Inject photo via CDP
python inject_photo_cdp.py

# Update Notion with published URL
python update_notion_url.py <notion_page_id> <listing_url>
```

## Photo Upload — CDP Injection

The photo upload uses a unique CDP-based injection method:
1. Connects to Chrome via WebSocket at `http://127.0.0.1:18800/json`
2. Encodes image as base64
3. Injects via `DataTransfer` + React fiber `onChange` trigger
4. Works for any image source URL (CDN, CORS-restricted hosts)

## Agent Skill

This is an **OpenClaw agent skill** — triggered by cron/job and executed through the local Python/CDP pipeline.

### Important

The production Milanuncios flow does **not** rely on `browser.act()` form filling anymore.
The stable path is:
- open publish form in profile `mixmix` on port `18801`
- inject photo via `inject_photo_cdp.py`
- fill and publish via CDP scripts (`publish_one.py`, `publish_via_cdp.py`, `fill_form_cdp.py`)

Do not use old experimental snippets that call `browser.act(action="act", fields=[...])`, `browser.act(kind="fill", text=...)`, or calls without `request.ref/selector`. Those snippets are legacy experiments and produce noisy browser-tool errors while the real publication can still succeed via CDP.

---

*Part of the AI automation toolkit for e-commerce operations (MixMix Spain).*
