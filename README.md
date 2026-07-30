# Скрин 1С без «КОРП»

В заголовке окна убрано слово **КОРП**.

**Было:** `Управление холдингом, редакция 3.3 (1С:Предприятие КОРП)`  
**Стало:** `Управление холдингом, редакция 3.3 (1С:Предприятие)`

## Результат

- `images/1c-osv-zagolovok-bez-korp.png` — отредактированный скриншот оборотно-сальдовой ведомости

## Свои исходники

Положите PNG в `images/original/` и запустите:

```bash
pip install -r requirements.txt
python3 scripts/remove_korp_from_title.py images/original -o images
```
