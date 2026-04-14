# Публикация товара в Milanuncios - Пошаговые инструкции

## Товар для публикации:
- **Название:** BHHB Unidades externas de CD y DVD con Bolsa de Almacenamiento, Unidad
- **Цена:** 13 EUR
- **Описание:** Unidad Externa CD/DVD
- **Вес:** 0.51kg (категория: Entre 500g y 1kg)
- **Состояние:** Practicamente nuevo

---

## ШАГИ ПУБЛИКАЦИИ:

### 1. ЗАПОЛНИТЬ НАЗВАНИЕ
Найти поле "Título del anuncio" и вввести:
```
BHHB Unidades externas de CD y DVD con Bolsa de Almacenamiento, Unidad
```

### 2. ЗАПОЛНИТЬ ОПИСАНИЕ
Найти текстовое поле описания и ввести:
```
Unidad Externa CD/DVD
```

### 3. ЗАПОЛНИТЬ ЦЕНУ
Найти поле "Precio" и ввести:
```
13
```

### 4. ВЫБРАТЬ СОСТОЯНИЕ
Найти dropdown "Estado del articulo" и выбрать:
```
Practicamente nuevo
```

### 5. ВЫБРАТЬ ВЕС
Найти поле "Peso" и выбрать категорию:
```
Entre 500g y 1kg
```

### 6. ОПУБЛИКОВАТЬ
Кликнуть кнопку "Publicar anuncio" или "Siguiente"

### 7. ДОЖДАТЬСЯ УСПЕХА
Страница должна показать "Enhorabuena, tu anuncio..."

### 8. СКОПИРОВАТЬ URL
URL товара будет в формате:
```
https://www.milanuncios.com/anuncios/rXXXXXXXX.htm
```

---

## ТЕХНИЧЕСКИЕ КОМАНДЫ (когда расширение подключится):

```python
# Заполнить название
browser.act(request={"kind": "type", "selector": "input[placeholder*='Titulo']", "text": "BHHB Unidades..."})

# Заполнить описание
browser.act(request={"kind": "type", "selector": "textarea", "text": "Unidad Externa CD/DVD"})

# Заполнить цену
browser.act(request={"kind": "type", "selector": "input[type='number']", "text": "13"})

# Выбрать вес
browser.act(request={"kind": "click", "selector": "select"})
browser.act(request={"kind": "type", "text": "Entre 500g"})

# Опубликовать
browser.act(request={"kind": "click", "selector": "button[type='submit']"})
```
