
# Most Sold Stock Items

> Total quantity dispensed, selling price, purchase price, and margin per stock item

## Purpose

Identifies the most-selling stock items by aggregating dispensed quantities and computing the gross margin (selling price minus purchase cost).

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `stock_name` | TEXT | Filter by stock item name (exact match) | `'Paracetamol'` |
| `DATE` | DATE | Filter by date range on the charge item | `2026-05-01` |

---

## Query

```sql
SELECT 
    pk.name AS stock_name,
    SUM(md.quantity) AS total_quantity_dispensed,
    SUM(ci.total_price) AS selling_price,
    SUM(p.purchase_price * md.quantity) AS purchase_price,
    SUM(ci.total_price - (p.purchase_price * md.quantity)) AS total_margin  
FROM emr_medicationdispense md
JOIN emr_chargeitem ci ON md.charge_item_id = ci.id         
JOIN emr_chargeitemdefinition cid ON ci.charge_item_definition_id = cid.id 
JOIN emr_product p ON p.charge_item_definition_id = cid.id
JOIN emr_productknowledge pk ON p.product_knowledge_id = pk.id
WHERE md.status IN ('completed', 'in_progress', 'preparation')  
  AND md.deleted = FALSE                                         
  AND ci.status IN ('billed', 'paid')
  --[[AND pk.name = {{stock_name}}]]
  --[[AND {{DATE}}]]  
GROUP BY pk.name
ORDER BY total_quantity_dispensed DESC;
```


## Notes

- Only non-deleted medication dispenses are included.
- Dispense status is filtered to `completed`, `in_progress`, and `preparation` to capture both fulfilled and active dispenses.
- Charge item status is filtered to `billed` and `paid` to ensure only items that have generated revenue are counted.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- Results are ordered by highest dispensed quantity first.

*Last updated: 2026-05-12*


