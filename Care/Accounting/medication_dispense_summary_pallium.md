
# Medication Dispense Summary - Pallium

> Aggregated medication dispense summary by medicine with total quantity dispensed and total revenue

## Purpose

Summary view of completed medication dispenses at Pallium, grouped by medicine. Each row shows the total quantity dispensed and total billed amount for a medicine.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created_date` | DATE / range | Metabase date filter (bound to `md.created_date`) | `'2026-05-25'` |

---

## Query

```sql
SELECT
    pk.name AS medicine_name,
    SUM(ci.total_price) AS total_price,
    SUM(md.quantity) AS total_quantity_dispensed
FROM emr_medicationdispense md
JOIN emr_chargeitem ci ON md.charge_item_id = ci.id
JOIN emr_chargeitemdefinition cid ON ci.charge_item_definition_id = cid.id
JOIN emr_product p ON p.charge_item_definition_id = cid.id
JOIN emr_productknowledge pk ON p.product_knowledge_id = pk.id
WHERE md.status = 'completed'
AND ci.status IN ('billed','paid')
  --[[AND {{created_date}}]]
GROUP BY pk.name
ORDER BY total_quantity_dispensed DESC;
```

## Notes

- **Metabase filters:**
  - `[[AND {{created_date}}]]` is a field filter — bind it to `md.created_date` in the Metabase variable settings.
- Only dispenses with `status = 'completed'` are included.

*Last updated: 2026-06-09*
