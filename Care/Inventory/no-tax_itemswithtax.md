
# No-Tax Category Items With Tax Report

> Active stock items in the "No-Tax" category (category_id = 6) that have tax factor configured

## Purpose

Identifies charge item definitions that belong to the "No-Tax" resource category (`category_id = 6`) but have a non-null CGST factor in their `price_components`.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `item_name` | TEXT (multi) | Filter by one or more stock item titles | `'Bandage', 'Cotton Roll'` |

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
  AND cid.category_id = 6
  AND prices.cgst_factor IS NOT NULL
  --[[AND cid.title IN ({{item_name}})]]
ORDER BY rc.title, cid.title;
```

## Notes

- Only active, non-deleted charge item definitions are returned (`cid.deleted = FALSE` AND `cid.status = 'active'`).
- Hardcoded to `category_id = 6` which represents the No-Tax category — update if the category ID changes.
- Price and tax values are extracted from the `price_components` JSONB 
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards
- Results are ordered by category, then stock name.

*Last updated: 2026-04-22*

````
