
# Stock in Air - SSMM

> In-transit stock deliveries (in-progress) with product, quantity, route, and creator details

## Purpose

Lists stock deliveries that are currently `in_progress` ("stock in air") at SSMM, showing what product is moving, quantity, delivery/order status, delivery record created date, origin and destination locations, and the user who created the delivery record.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE / range | Metabase date filter (typically bound to `esd.created_date`) | `'2026-08-01'` |

---

## Query

```sql
SELECT
	epk.name AS product_name,
	esd.supplied_item_quantity AS supplied_qty,
	esd.status AS delivery_status,
	edo.status AS order_status,
	esd.created_date AS delivery_date,
	origin.name AS origin,
	destination.name AS destination,
	CONCAT(uu.first_name, ' ', uu.last_name) AS delivery_created_by
FROM emr_supplydelivery esd
JOIN emr_deliveryorder edo
	ON esd.order_id = edo.id
JOIN emr_inventoryitem eii
	ON esd.supplied_inventory_item_id = eii.id
JOIN emr_product ep
	ON eii.product_id = ep.id
JOIN emr_productknowledge epk
	ON ep.product_knowledge_id = epk.id
 JOIN emr_facilitylocation origin
	ON origin.id = edo.origin_id
   AND origin.deleted = FALSE
 JOIN emr_facilitylocation destination
	ON destination.id = edo.destination_id
   AND destination.deleted = FALSE
LEFT JOIN users_user uu
	ON uu.id = esd.created_by_id
WHERE esd.status = 'in_progress'
  --[[AND {{date}}]]
ORDER BY epk.name;
```

## Notes

- **"Stock in air" definition:** This query treats any supply delivery with `esd.status = 'in_progress'` as in-transit stock.
- **Metabase filter:** `[[AND {{date}}]]` is a field filter — bind it to `esd.created_date`.
- Results are ordered alphabetically by `product_name`.

*Last updated: 2026-08-13*
