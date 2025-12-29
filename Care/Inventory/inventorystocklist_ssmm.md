# Inventory Stock List

> Current inventory stock levels with location, expiry dates, and low stock alerts

## Purpose

This query provides a comprehensive view of inventory items across all locations, showing current stock quantities, expiration dates, and flagging low stock items. It's useful for inventory management, reordering decisions, and identifying items nearing expiration.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `stock_name` | TEXT | Filters by product name  | `'bandage'` |

---

## Query

```sql
SELECT
  pk.name AS stock_name,
  fl.name AS location_name,
  ii.net_content AS quantity,
  p.expiration_date AS expiry_date,
  CASE 
    WHEN ii.net_content < 100 THEN 'Low Stock'
    ELSE ' '
  END AS stock_status
FROM emr_inventoryitem ii
 JOIN emr_facilitylocation fl ON ii.location_id = fl.id
LEFT JOIN emr_product p ON ii.product_id = p.id
LEFT JOIN emr_productknowledge pk ON p.product_knowledge_id = pk.id
WHERE 1=1
--   [[AND LOWER(pk.name) ILIKE '%' || LOWER({{stock_name}}) || '%']]
ORDER BY ii.net_content ASC;
```


## Notes

- Hardcoded at 100 units - items below this threshold are flagged as 'Low Stock'
- Results are ordered by quantity (lowest first) to prioritize low stock items
- Uses product knowledge table for standardized product names

*Last updated: 2025-12-29*
