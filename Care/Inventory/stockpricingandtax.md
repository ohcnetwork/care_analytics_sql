
# Stock Pricing and Tax Report

> Detailed list of active stock items with base price and CGST/SGST tax components

## Purpose

Provides a comprehensive view of active charge item definitions (stock items) along with their resource category, base price, and tax components (CGST and SGST factors).

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `item_name` | TEXT (multi) | Filter by one or more stock item titles | `'Paracetamol 500mg', 'Amoxicillin 250mg'` |
| `category` | TEXT (multi) | Filter by one or more resource category titles | `'Medicines', 'Consumables'` |
| `cgst_factor` | NUMERIC | Filter by an exact CGST factor value | `2.5` |

---

## Query

```sql
SELECT 
    cid.title AS stock_name,
    rc.title AS category,
    prices.base_amount AS base_price,
    prices.cgst_factor,
    prices.sgst_factor
FROM emr_chargeitemdefinition cid
JOIN emr_resourcecategory rc ON cid.category_id = rc.id
LEFT JOIN LATERAL (
    SELECT 
        MAX(CASE WHEN pc ->> 'monetary_component_type' = 'base' 
            THEN (pc ->> 'amount')::numeric END) AS base_amount,
        MAX(CASE WHEN pc ->> 'monetary_component_type' = 'tax' 
            AND pc -> 'code' ->> 'display' = 'CGST' 
            THEN (pc ->> 'factor')::numeric END) AS cgst_factor,
        MAX(CASE WHEN pc ->> 'monetary_component_type' = 'tax' 
            AND pc -> 'code' ->> 'display' = 'SGST' 
            THEN (pc ->> 'factor')::numeric END) AS sgst_factor
    FROM jsonb_array_elements(cid.price_components) AS pc
) prices ON true
WHERE cid.deleted = FALSE
  AND cid.status = 'active'
  AND cid.category_id IN (17, 18, 6, 62)
  --[[AND cid.title IN ({{item_name}})]]
  --[[AND rc.title IN ({{category}})]]
  --[[AND prices.cgst_factor = {{cgst_factor}}::numeric]]
ORDER BY rc.title, cid.title;
```


## Notes

- Only active, non-deleted charge item definitions are returned (`cid.deleted = FALSE` AND `cid.status = 'active'`).
- The query is hardcoded to `category_id IN (17, 18, 6, 62)` update these IDs based on requirement.
- Price and tax values are extracted from the `price_components` JSONB column
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards
- Results are ordered by category, then stock name.

*Last updated: 2026-04-22*

````
