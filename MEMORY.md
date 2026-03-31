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

## Инциденты

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
