# Milanuncios Poster — Project Memory

**Статус:** PRODUCTION — ежедневный cron в 14:00 Madrid
**Последнее обновление:** 2026-03-10

---

## Текущее состояние
- Cron `milanuncios_daily_poster` (ID: `211a6e98`) — каждый день 14:00
- Публикует 5-7 товаров/день из Notion
- Отчёты → **Telegram топик 4** (торговля)
- Zello уведомления через notify_queue.json
- **Cleanup:** `cleanup_milanuncios.py` — проверка всех условий (In Stock, цена, donde, sold, archived)
  - Запускается автоматически в начале крона (ЧАСТЬ 0)
  - Очищает Notion-поля + выдаёт Notion/Milanuncios ссылки в отчёт для ручного удаления

## Золотое правило
**БЕЗ ФОТО — НЕ ПУБЛИКОВАТЬ.** Никогда. Без исключений.

## Workflow (полный)
```
1. cleanup_sold_products.py     — удалить проданное
2. fetch_product_for_milanuncios.py — взять товар из Notion
3. browser → https://www.milanuncios.com/publicar-anuncios-gratis/publicar?c=447
4. inject_photo_cdp.py          — загрузить фото через CDP
   → NO_IMAGE / ERROR = пропустить товар
5. Заполнить форму + опубликовать
6. update_notion_url.py <notion_id> <url> — обновить Notion
7. Ждать 20 сек → следующий товар
```

## Ключевые файлы
- `fetch_product_for_milanuncios.py` — получение товара из Notion
- `inject_photo_cdp.py` — инжектор фото через CDP (порт 18801 по умолчанию, поддерживает --port)
- `cleanup_milanuncios.py` — полная проверка условий (NEW, 29.03.2026)
- `cleanup_sold_products.py` — очистка проданных (old, для browser-delete)
- `update_notion_url.py` — запись URL в Notion
- `temp/product_data.json` — текущий товар
- `temp/` — все временные файлы

## Cron job
- ID: `211a6e98-a3d3-4c88-913f-8e51fc1226f1`
- Schedule: `0 14 * * *` Europe/Madrid
- Model: `anthropic/claude-sonnet-4-6`
- Timeout: 1800 сек (30 мин)
- Delivery: агент сам отправляет в Telegram топик 4

## ⚠️ Баг 30.03.2026 — Фото грузились в один таб
**Причина:** `inject_photo_cdp.py` искал ПЕРВЫЙ таб с `milanuncios.com` вместо таба с формой `/publicar-anuncios-gratis/publicar`. Браузер имел 5+ табов Milanuncios → все 7 фото шли в один таб, а 7 товаров публиковались без фото.
**Фикс:** Селектор теперь ищет ТОЛЬКО `/publicar-anuncios-gratis/publicar`. Fallback с WARNING если не найден.
**Правило для агента:** Каждый товар = НОВЫЙ таб формы → inject фото → заполнить → опубликовать → ЗАКРЫТЬ таб.

## ⚠️ Инцидент 13.04.2026 — шумные browser.act ошибки при рабочей публикации
**Симптом:** в логах шли ошибки вида `browser failed: request required`, `ref or selector is required`, `fields are required`, `locator.type timeout`, хотя публикации в профиле `mixmix` по факту проходили успешно.
**Первопричина:** в проекте и связанных промптах оставались legacy-эксперименты с `browser.act()` для Milanuncios. Они использовали неверный формат вызова (`action="act"` без `request`, `kind="fill"` с `text` вместо `fields`, вызовы без `ref/selector`, старые refs вроде `e8/e9/e18`). Эти вызовы шумели в логах, но реальная публикация шла через отдельный CDP pipeline (`inject_photo_cdp.py` + `publish_one.py` / `publish_via_cdp.py`).
**Вывод:** проблема была не в том, что открывался не тот профиль, а в смешении двух подходов: старого browser-tool сценария и рабочего CDP сценария.
**Правило:** для боевого Milanuncios использовать только CDP pipeline. Legacy `browser.act()` snippets считать справочными/историческими, не использовать в production.

## Инциденты

### 28.04.2026 — UnicodeEncodeError + дубли из-за Notion latency
- `publish_one.py` падал на `print("Title:", r)` при акцентированных символах в cp1251-консоли Windows после успешной загрузки фото и заполнения заголовка.
- Фикс: backup `temp/publish_one.py.bak-20260428-encoding`, добавлен `sys.stdout/stderr.reconfigure(encoding='utf-8', errors='replace')`, `python -m py_compile publish_one.py` OK.
- В этом запуске `publish_one.py` всё ещё возвращал предыдущий top ad URL, поэтому после batch нужно сверять `get_top_ads.py` и корректировать Notion URL. 28.04 первые 4 URL скорректированы вручную.
- Из-за задержки обновления Notion один товар Oral-B iO 10 опубликовался повторно (2 дополнительных объявления). Нужен следующий техфикс: после успешного update делать локальный seen-set по notion_id и/или sleep/verify Notion before next fetch.

### 20.03.2026 — Chromium заморозка (CDP)
- **Результат:** 0 из 7 опубликовано
- **Причина:** `inject_photo_cdp.py` загрузил фото (86 KB) и начал инжект JS (116 KB) → CDP перестал отвечать
- **Решение:** Убиты 32 процесса Chromium, перезапущен профиль mixmix (18801) и openclaw (18800)
- **TODO:** Проверить openclaw профиль (18800) перед следующим job — перезапустить если завис

---

## Изменения в сессии 09.03.2026
- ✅ Отчёты переведены в **Telegram топик 4** (было: главный чат)
- Delivery mode изменён на `none` (агент сам шлёт через message tool)

## Telegram отчёт
```
📊 Итоговый отчёт — Milanuncios Daily Job ([дата])
ЧАСТЬ 1 — Очистка: Удалено: N
ЧАСТЬ 2 — Опубликовано: N из 7
[таблица товаров]
Пропущено: [причины]
Осталось в очереди: ~N
```
Отправляется в: chat=-1003319033023, threadId="4"

## Estado товаров
- ВСЕГДА "Prácticamente nuevo" (не менять!)

## ⚠️ Инцидент 26.03.2026 — 0 опубликовано
- Профиль `openclaw` НЕ залогинен на Milanuncios (нужен `mixmix`)
- Крон `milanuncios_daily_poster` использовал openclaw вместо mixmix → пофикшен 26.03
- Wallapop: 8 опубликовано ✅, 2 пропущено (фото 403 — ABUS, COSORI)

## Связанные файлы в папке
- `README.md` — полная документация
- `temp/` — временные файлы (чистить после сессии)

### 29.04.2026 — Daily job safe stop after 1 publish
- Cleanup cleared 1 non-compliant listing in Notion: Intex 58849NP (out_of_stock). Manual Milanuncios deletion still needed: https://www.milanuncios.com/otros-articulos-de-menaje/tobogan-hinchable-intex-591870047.htm
- cleanup_sold_products count=0.
- Published Intex 28637: https://www.milanuncios.com/anuncios/r592686111.htm.
- Important: after update_notion_url OK, fetch_product_for_milanuncios still returned the same Intex 28637 with Milanuncios Posted populated. Job was stopped to avoid duplicate listing. Need fix/verify fetch filter or Notion latency handling before next mass run.
- Telegram topic 4 report sent (message_id 13592), Zello queued.

### 30.04.2026 — Daily job cleanup only, no products
- cleanup_milanuncios cleared 2 non-compliant listings in Notion, both `out_of_stock`:
  - Cecotec Cepillo de Aire Secador Moldeador Alisador Multifunción 8 Cabezales CeramicCare AirGlam Champagne → https://www.milanuncios.com/anuncios/r592420849.htm
  - Cecotec Limpiador Aspirador de Tapicerias y Alfombras Conga 7000 Carpet&Spot Clean Steam XXL → https://www.milanuncios.com/anuncios/r591025904.htm
- cleanup_sold_products count=0.
- `fetch_product_for_milanuncios.py` returned `NO_PRODUCTS`, so 0/7 published.
- Telegram topic 4 report sent (message_id 13666), Zello queued.

### 01.05.2026 — Daily job cleanup only, no products
- cleanup_milanuncios: to_delete=0, ok=231, errors=0.
- cleanup_sold_products count=0.
- `fetch_product_for_milanuncios.py` returned `NO_PRODUCTS`, so 0/7 published.
- Zello queued.
- Telegram delivery issue: local Telegram Gateway cannot resolve `-1003319033023#4`; `sessions_send` to topic 4 timed out via gateway `18789`. Report text was prepared but topic delivery could not be confirmed from this cron runtime.

### 05.05.2026 — Daily job successful, 5 published
- cleanup_milanuncios --execute: to_delete=1, ok=230, deleted=1, errors=0.
- Единственный cleared item: NEEWER Panel de Luz LED Softbox..., reason=`out_of_stock`, `milanuncios_url=https://www.milanuncios.com/anuncios/pending_review_neewer`; поскольку URL не был реальным `/anuncios/r...`, ручное удаление на сайте не потребовалось.
- cleanup_sold_products returned `count=1` for the same NEEWER item. Browser check in profile `mixmix` opened a Milanuncios 404 page (`¡Vaya! No hemos encontrado esta página`), после чего запись очищена через `cleanup_sold_products.py --clear 2ec12f74-2f9e-81b7-b9ba-f55a43308241`.
- Published 5/7 via `mixmix` profile on port `18801` using `inject_photo_cdp.py --port 18801` + `publish_via_cdp.py`:
  1. Portabicicletas para 3 bicicletas con enganche, 20€ → https://www.milanuncios.com/anuncios/r592940710.htm
  2. Impresora de inyección de tinta multifunción Expression A4..., 35€ → https://www.milanuncios.com/anuncios/r593827763.htm
  3. Adaptador para calentador de agua, 18€ → https://www.milanuncios.com/anuncios/r593827833.htm
  4. Silverline Tools 783171 Cama para mecánico 920 mm, 22€ → https://www.milanuncios.com/anuncios/r593827871.htm
  5. iRobot Braava 380t, 33€ → https://www.milanuncios.com/anuncios/r593827917.htm
- No skips, no publish errors.
- Telegram topic 4 report sent successfully via direct Telegram Bot API (`message_id 13775`). Zello queued. Fetch still showed `remaining~100+`, so queue is healthy.

### 06.05.2026 — Daily job successful, 5 published
- cleanup_milanuncios --execute: to_delete=0, ok=235, deleted=0, errors=0.
- cleanup_sold_products returned `count=0`.
- Published 5/7 via `mixmix` profile on port `18801` using `inject_photo_cdp.py --port 18801` + `publish_one.py`:
  1. MidWest Homes for Pets modelo 550-36DR..., 26.95€ → https://www.milanuncios.com/anuncios/r593827943.htm
  2. Trunki Ride-On Suitcase Blue/Green/Orange, 20€ → https://www.milanuncios.com/anuncios/r593994667.htm
  3. Cecotec Limpiacristales Aspirador de Ventanas Conga Rockstar 3700 Glass..., 22.36€ → https://www.milanuncios.com/anuncios/r593995027.htm
  4. Baseus Super Energy Car Jump Starter 10000mAh 1000A, 40€ → https://www.milanuncios.com/anuncios/r593995453.htm
  5. H.Koenig Limpiador a Vapor 4 barras NV6400..., 49.95€ → https://www.milanuncios.com/anuncios/r593995898.htm
- No skips, no publish errors.
- Telegram topic 4 report sent successfully via direct Telegram Bot API (`message_id 13779`). Zello queued. Fetch still showed `remaining~100+`, so queue is healthy.

### 07.05.2026 — Daily job published 5, but URL capture drift returned
- cleanup_milanuncios --execute: to_delete=0, ok=240, deleted=0, errors=0.
- cleanup_sold_products returned `count=0`.
- Attempted/published 5/7 via `mixmix` profile on port `18801` using `inject_photo_cdp.py --port 18801` + `publish_via_cdp.py`:
  1. Cámara 360 de videovigilancia WiFi compacta..., 32€ → https://www.milanuncios.com/anuncios/r593996215.htm
  2. Mobiclinic pets carrito para perros..., 34€ → https://www.milanuncios.com/anuncios/r594187004.htm
  3. Samsung SOLO Box Galaxy Buds Live, 20€ → https://www.milanuncios.com/anuncios/r594187042.htm
  4. EGLO LATERRA 3, 27€ → script returned the same URL https://www.milanuncios.com/anuncios/r594187042.htm
  5. Precaster Hora S2, 53€ → https://www.milanuncios.com/anuncios/r594187142.htm
- Verification with `get_top_ads.py` immediately after run showed title↔URL drift/lag: top list displayed `EGLO LATERRA 3`, `MOBICLINIC PETS...`, `CÁMARA 360...`, while Samsung/Precaster were not clearly verifiable by fresh top-ad titles. So publication itself likely happened, but Notion URL mapping for the last 3 items cannot be trusted without manual Milanuncios check.
- Telegram topic 4 report sent via direct Telegram Bot API. Zello queued.

### 09.05.2026 — Daily job successful, 5 published
- cleanup_milanuncios --execute: to_delete=2, ok=249, deleted=2, errors=0.
- Cleared items in Notion: two Keter Jaipur loungers with `out_of_stock`; only one had a real manual-delete Milanuncios URL: https://www.milanuncios.com/anuncios/r590224604.htm . The second was legacy `/otros-articulos-de-menaje/...` and was not included in manual-delete list.
- cleanup_sold_products returned `count=0`.
- Published 5/7 via `mixmix` profile on port `18801` using `inject_photo_cdp.py --port 18801` + `publish_via_cdp.py`:
  1. Conga Windroid 1290 Double Spray Connected, 79.5€ → https://www.milanuncios.com/anuncios/r594335894.htm
  2. Logitech G Pro X SE..., 40€ → https://www.milanuncios.com/anuncios/r594481318.htm
  3. Rowenta Turbo Silence Extreme VU5675..., 88.03€ → https://www.milanuncios.com/anuncios/r594481363.htm
  4. Kensington VeriMark Guard USB-C..., 33€ → https://www.milanuncios.com/anuncios/r594481396.htm
  5. Moulinex Subito Select..., 35.25€ → https://www.milanuncios.com/anuncios/r594481438.htm
- No skips, no publish errors.
- Telegram topic 4 report sent via direct Telegram Bot API (`message_id 13821`). Zello queued. Fetch still showed `remaining~100+`, so queue remains healthy.

