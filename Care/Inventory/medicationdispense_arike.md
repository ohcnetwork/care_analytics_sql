# Medication Dispense - Arike

> Summary of medication dispenses by location, medicine, and batch with quantities

## Purpose

This query provides a detailed view of medication dispensing activity, showing how much of each medicine (by batch) has been dispensed from each location. It's useful for inventory tracking, stock management, and understanding medication usage patterns across different facility locations.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filters dispenses by creation date | `DATE(md.created_date) = '2026-01-09'` |
| `location_filter` | TEXT | Filters by facility location name | `'Pharmacy'` |
| `medicine_filter` | TEXT | Filters by medicine/product name | `'Paracetamol'` |

---

## Query

```sql
SELECT 
    fl.name AS location_name,
    pk.name AS medicine_name,
    p.batch->>'lot_number' AS batch,
    p.expiration_date AS expiry,
    ii.net_content,
    SUM(md.quantity) AS total_quantity_dispensed  
FROM emr_medicationdispense md
JOIN emr_facilitylocation fl 
    ON md.location_id = fl.id
JOIN emr_inventoryitem ii 
    ON md.item_id = ii.id
JOIN emr_product p 
    ON ii.product_id = p.id
JOIN emr_productknowledge pk 
    ON p.product_knowledge_id = pk.id
WHERE md.deleted = FALSE
--   [[AND {{date}}]]
--   [[AND fl.name = {{location_filter}}]]
--   [[AND pk.name = {{medicine_filter}}]]
GROUP BY 
    fl.name,
    pk.name,
    p.batch->>'lot_number',
    p.expiration_date,
    ii.net_content
ORDER BY fl.name DESC;
```


## Notes

- Only includes active medication dispenses (deleted = FALSE)
- Net content shows the current inventory level, while total_quantity_dispensed shows historical dispenses

*Last updated: 2026-01-09*
