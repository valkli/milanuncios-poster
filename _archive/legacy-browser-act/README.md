# legacy-browser-act

Архив старых экспериментальных сценариев Milanuncios через `browser.act()`.

Почему убрано из `temp/`:
- давали ложный сигнал, будто это рабочий production path
- содержали устаревший формат browser tool вызовов
- провоцировали шумные ошибки вида `request required`, `fields are required`, `ref or selector is required`

Текущий production path для Milanuncios:
- `inject_photo_cdp.py`
- `publish_one.py`
- `publish_via_cdp.py`
- `fill_form_cdp.py`

Эти legacy-файлы хранить только как архив/историю, не использовать в cron и не использовать как инструкцию для агента.
