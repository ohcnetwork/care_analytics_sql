# Inventory Stock by Location

> Monitor inventory stock levels across facility locations with expiration date tracking

## Purpose

Track and analyze inventory stock distribution across facility locations, including expiration date monitoring. Helps identify stock levels, expiration status, and inventory management across care facilities.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `expiry_flag` | TEXT | Filter by expiration status | `Expired` or `Critical - Expires in 1 month` |

---

## Query

```sql
SELECT 
    fl.name AS location_name,
    pk.name AS stock_name,
    TO_CHAR(p.expiration_date, 'DD/MM/YYYY') AS expiration_date,
    p.batch->>'lot_number' AS batch_number,
    CASE 
        WHEN p.expiration_date <= CURRENT_DATE THEN 'Expired'
        WHEN p.expiration_date <= CURRENT_DATE + INTERVAL '1 month' THEN 'Critical - Expires in 1 month'
        WHEN p.expiration_date <= CURRENT_DATE + INTERVAL '3 months' THEN 'Warning - Expires in 3 months'
        ELSE ''
    END AS expiry_flag,
    ii.net_content AS stock_count
FROM emr_productknowledge pk
JOIN emr_product p ON p.product_knowledge_id = pk.id
JOIN emr_inventoryitem ii ON ii.product_id = p.id
JOIN emr_facilitylocation fl ON ii.location_id = fl.id
WHERE 
    fl.deleted = FALSE
    AND pk.deleted = FALSE
    --   [[AND
    --     CASE 
    --       WHEN p.expiration_date <= CURRENT_DATE THEN 'Expired'
    --       WHEN p.expiration_date <= CURRENT_DATE + INTERVAL '1 month' THEN 'Critical - Expires in 1 month'
    --       WHEN p.expiration_date <= CURRENT_DATE + INTERVAL '3 months' THEN 'Warning - Expires in 3 months'
    --       ELSE ''
    --     END = {{expiry_flag}}
    --   ]]
ORDER BY 
    fl.name,
    pk.name,
    expiration_date;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- Expiration status is determined using CASE logic with three warning levels:
  - **Expired**: Expiration date is today or in the past
  - **Critical - Expires in 1 month**: Expiration within 1 month from today
  - **Warning - Expires in 3 months**: Expiration within 3 months from today
  - **Empty**: Stock that does not fall into any warning category
- Only non-deleted facility locations and product knowledge records are included in results.
- Batch/lot numbers are extracted from the JSONB `batch` field
- The `net_content` field represents the current stock quantity at each location.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
