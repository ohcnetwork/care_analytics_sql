
# Taxable Category Items With No Tax Allocated

> Active stock items in the 5% / 18% GST categories (category_id IN (17, 18)) that have no tax component configured in their price_components

## Purpose

Identifies charge item definitions that belong to taxable resource categories (5% GST = `category_id 17`, 18% GST = `category_id 18`) but have **no tax component** present in their `price_components` JSONB.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `item_name` | TEXT (multi) | Filter by one or more stock item titles | `'Paracetamol 500mg', 'Surgical Gloves'` |

---

## Query

```sql
SELECT 
    cid.title AS charge_item_name,
    cid.status,
    rc.title AS category,
    (SELECT (pc ->> 'amount')::numeric
     FROM jsonb_array_elements(cid.price_components) AS pc
     WHERE pc ->> 'monetary_component_type' = 'base'
     LIMIT 1
    ) AS base_price
FROM emr_chargeitemdefinition cid
LEFT JOIN emr_resourcecategory rc ON cid.category_id = rc.id
WHERE cid.deleted = FALSE
  AND cid.status = 'active'
  AND cid.category_id IN (17, 18)
  AND NOT EXISTS (
      SELECT 1
      FROM jsonb_array_elements(cid.price_components) AS pc
      WHERE pc ->> 'monetary_component_type' = 'tax'
  )
  --[[AND cid.title IN ({{item_name}})]]
ORDER BY rc.title, cid.title;
```

## Notes

- Only active, non-deleted charge item definitions are returned (`cid.deleted = FALSE` AND `cid.status = 'active'`).
- Hardcoded to `category_id IN (17, 18)` — the taxable GST categories. Update if the category IDs change.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards
- Results are ordered by category, then charge item name.

*Last updated: 2026-04-22*

````
