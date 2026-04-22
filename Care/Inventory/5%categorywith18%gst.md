
# 5% GST Category Items With 18% GST 

> Active stock items in the 5% GST category (category_id = 17) With 18% GST, typically misconfigured with 18% GST or another rate

## Purpose

Identifies charge item definitions that belong to the 5% GST resource category (`category_id = 17`) but have a CGST factor different from the expected. 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `item_name` | TEXT (multi) | Filter by one or more stock item titles | `'Paracetamol 500mg', 'ORS Sachet'` |

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
  AND cid.category_id = 17
  AND prices.cgst_factor != 2.5
  --[[AND cid.title IN ({{item_name}})]]
ORDER BY rc.title, cid.title;
```


## Notes

- Only active, non-deleted charge item definitions are returned (`cid.deleted = FALSE` AND `cid.status = 'active'`).
- Hardcoded to `category_id = 17` which represents the 5% GST category — update if the category ID changes.
- Price and tax values are extracted from the `price_components` JSONB
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards
- Results are ordered by category, then stock name.

*Last updated: 2026-04-22*

````
