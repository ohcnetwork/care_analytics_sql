
# Medication Dispense Report - Pallium

> Line-level medication dispense report with location, batch, expiry, ans dispensing staff

## Purpose

Detailed view of completed medication dispenses at Pallium. Each row is one dispense and includes the inventory location, product / batch / expiry, who dispensed it.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE / range | Metabase date filter (typically bound to `md.created_date`) | `'2026-05-25'` |
| `location_filter` | TEXT | Filter by inventory location name (exact match) | `'Pharmacy'` |
| `medicine_filter` | TEXT | Filter by medicine / product name (exact match) | `'Paracetamol'` |

---

## Query

```sql
SELECT 
    fl.name AS location_name,
    pk.name AS medicine_name,
    p.batch->>'lot_number' AS batch,
    p.expiration_date AS expiry,
    md.created_date,
    TRIM(u.first_name || ' ' || u.last_name) AS created_by_name,
    md.quantity AS dispensed_quantity
FROM emr_medicationdispense md
JOIN emr_inventoryitem ii ON md.item_id = ii.id
JOIN emr_product p ON ii.product_id = p.id
JOIN emr_productknowledge pk ON p.product_knowledge_id = pk.id
JOIN emr_facilitylocation fl ON ii.location_id = fl.id
JOIN users_user u ON md.created_by_id = u.id
WHERE md.status = 'completed'
  --[[AND {{date}}]]
  --[[AND fl.name = {{location_filter}}]]
  --[[AND pk.name = {{medicine_filter}}]]
ORDER BY md.created_date DESC;
```

## Notes


- **Metabase filters:**
  - `[[AND {{date}}]]` is a field filter — bind it to `md.created_date` in the Metabase variable settings.
  - `[[AND fl.name = {{location_filter}}]]` and `[[AND pk.name = {{medicine_filter}}]]` are exact-match text filters on inventory location and medicine name.


*Last updated: 2026-05-25*



