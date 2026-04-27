
# Inventory Stock by Location

> Total available quantity of each stock item, grouped by facility location

## Purpose

Provides a consolidated view of current inventory stock levels per facility location and stock item.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `stock_name` | TEXT | Filter by stock item name (prefix match, case-insensitive) | `'Paracetamol'` |
| `location` | TEXT (multi) | Filter by one or more facility location names | `'Pharmacy', 'Ward A Store'` |

---

## Query

```sql
SELECT 
    fl.name AS location_name,
    pk.name AS stock_name,
    SUM(ii.net_content) AS total_quantity
FROM emr_inventoryitem ii
JOIN emr_product p ON ii.product_id = p.id
JOIN emr_productknowledge pk ON p.product_knowledge_id = pk.id
JOIN emr_facilitylocation fl ON ii.location_id = fl.id
WHERE ii.deleted = FALSE
  --[[AND pk.name =  {{stock_name}} ]]
  --[[AND fl.name IN ({{location}})]]
GROUP BY fl.name, pk.name
ORDER BY fl.name, pk.name;
```


## Notes

- Only active inventory rows are included (`ii.deleted = FALSE`).
- The `location` filter accepts a multi-select list of location names.
- Quantities are aggregated using `SUM(ii.net_content)`, which can include multiple batches/lots of the same product at the same location.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards
- Results are ordered by location, then stock name.

*Last updated: 2026-04-22*

````
