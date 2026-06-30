
# Inventory Report

> Per-location, per-batch inventory snapshot with purchase value and expiry flagging

## Purpose

Returns a full inventory snapshot with one row per inventory item . Each row shows the stock count, batch number, expiration date, unit purchase price, total purchase value (`stock_count × purchase_price`), and an `expiry_flag` that buckets each batch as **Expired**, **Critical (≤1 month)**, **Warning (≤3 months)**, or normal.

---

## Query

```sql
SELECT
    fl.name AS location_name,
    pk.name AS stock_name,
    TO_CHAR(p.expiration_date, 'DD/MM/YYYY') AS expiration_date,
    p.purchase_price,
    ii.net_content * p.purchase_price AS total_purchase,
    p.batch ->> 'lot_number' AS batch_number,
    CASE
        WHEN p.expiration_date <= CURRENT_DATE THEN 'Expired'
        WHEN p.expiration_date <= CURRENT_DATE + INTERVAL '1 month'  THEN 'Critical - Expires in 1 month'
        WHEN p.expiration_date <= CURRENT_DATE + INTERVAL '3 months' THEN 'Warning - Expires in 3 months'
        ELSE ''
    END AS expiry_flag,
    ii.net_content AS stock_count
FROM emr_productknowledge pk
JOIN emr_product p
    ON p.product_knowledge_id = pk.id
JOIN emr_inventoryitem ii
    ON ii.product_id = p.id
JOIN emr_facilitylocation fl
    ON ii.location_id = fl.id
WHERE fl.deleted = FALSE
ORDER BY
    fl.name,
    pk.name,
    expiration_date;
```


## Notes
- Results are ordered by location, then stock name.

*Last updated: 2026-06-29*
