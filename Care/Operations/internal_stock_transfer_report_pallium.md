
# Internal Stock Transfer Report

> Line-level report of internal stock transfers between facility locations with batch, expiry, and quantity

## Purpose

Lists supply deliveries at Pallium that move stock **between two facility locations** (origin → destination). Each row shows the supply date, origin and destination locations, the product (with batch / lot number and expiry), and the quantity transferred.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE / range | Metabase date filter (typically bound to `sd.created_date`) | `'2026-06-01'` |
| `stock_name` | TEXT | Filter by product / stock name (exact match on `emr_productknowledge.name`) | `'Paracetamol'` |

---

## Query

```sql
SELECT
    DATE(sd.created_date) AS supply_date,
    fl_origin.name AS origin_location,
    fl_dest.name AS destination_location,
    p.batch ->> 'lot_number' AS lot_number,
    p.expiration_date,
    pk.name AS product_name,
    sd.supplied_item_quantity AS quantity_delivered
FROM emr_supplydelivery sd
JOIN emr_inventoryitem ii
    ON sd.supplied_inventory_item_id = ii.id
JOIN emr_product p
    ON ii.product_id = p.id
JOIN emr_productknowledge pk
    ON p.product_knowledge_id = pk.id
JOIN emr_deliveryorder d
    ON sd.order_id = d.id
JOIN emr_facilitylocation fl_origin
    ON d.origin_id = fl_origin.id
JOIN emr_facilitylocation fl_dest
    ON d.destination_id = fl_dest.id
WHERE sd.status NOT IN ('entered_in_error','abandoned')
  --[[AND {{date}}]]
  --[[AND pk.name = {{stock_name}}]]
ORDER BY supply_date DESC;
```

## Notes

- **Internal transfer scope:** Joining `emr_deliveryorder` on both `origin_id` and `destination_id` to `emr_facilitylocation` (via `fl_origin` and `fl_dest`) means only deliveries that have both a source and destination facility location are returned — i.e. internal transfers.
- Results are ordered by most recent `supply_date` first.

*Last updated: 2026-06-29*
