# Скрины 1С без «КОРП»

В заголовке убрано только слово **КОРП** (таблица и стили не менялись).

**Было:** `Управление холдингом, редакция 3.3 (1С:Предприятие КОРП)`  
**Стало:** `Управление холдингом, редакция 3.3 (1С:Предприятие)`

## Результаты

| Исходник | Результат |
|----------|-----------|
| `images/original/OSV_Eliminaciya_VGO_BANK_Eliminiruyushchiy.png` | `images/OSV_Eliminaciya_VGO_BANK_Eliminiruyushchiy_bez_korp.png` |
| `images/original/OSV_MSFO_AO_BANK.png` | `images/OSV_MSFO_AO_BANK_bez_korp.png` |
| `images/original/OSV_MSFO_AO_BANK_Eliminiruyushchiy.png` | `images/OSV_MSFO_AO_BANK_Eliminiruyushchiy_bez_korp.png` |
| `images/original/OSV_MSFO_AO_BANK_Konsolidirovannyy.png` | `images/OSV_MSFO_AO_BANK_Konsolidirovannyy_bez_korp.png` |
| `images/original/OSV_MSFO_AO_BANK_Obedinennyy.png` | `images/OSV_MSFO_AO_BANK_Obedinennyy_bez_korp.png` |
| `images/original/OSV_MSFO_OOO_DO1_korr.png` | `images/OSV_MSFO_OOO_DO1_korr_bez_korp.png` |
| `images/original/OSV_MSFO_OOO_DO2_bez_korr.png` | `images/OSV_MSFO_OOO_DO2_bez_korr_bez_korp.png` |
| `images/original/OSV_MSFO_OOO_DO2_korr.png` | `images/OSV_MSFO_OOO_DO2_korr_bez_korp.png` |
| `images/original/OSV_RSBU_OOO_DO1.png` | `images/OSV_RSBU_OOO_DO1_bez_korp.png` |
| `images/original/OSV_RSBU_OOO_DO1_kratko.png` | `images/OSV_RSBU_OOO_DO1_kratko_bez_korp.png` |
| `images/original/OSV_RSBU_OOO_DO2.png` | `images/OSV_RSBU_OOO_DO2_bez_korp.png` |
| `images/original/OSV_RSBU_OOO_DO2_kratko.png` | `images/OSV_RSBU_OOO_DO2_kratko_bez_korp.png` |
| `images/original/Otchetnost_MSFO_AO_BANK_Konsolidirovannyy.png` | `images/Otchetnost_MSFO_AO_BANK_Konsolidirovannyy_bez_korp.png` |
| `images/original/Otchetnost_MSFO_AO_BANK_Konsolidirovannyy_PuU.png` | `images/Otchetnost_MSFO_AO_BANK_Konsolidirovannyy_PuU_bez_korp.png` |

Всего: **14** файлов.

## Повторная обработка

```bash
python3 scripts/remove_korp_from_title.py images/original -o images
```
