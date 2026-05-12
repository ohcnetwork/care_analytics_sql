
# Internal Supply Delivery Purchase

> Daily purchase value and quantity of stock items received from a specific internal supplier, grouped by destination location and stock

## Purpose

Tracks stock supplied by a particular internal supplier organisation (`supplier_id = 20697`) to various destination locations within the facility.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created_date` | DATE | Filter deliveries by their created date | `2026-05-01` |
| `location` | TEXT (multi) | Filter by one or more destination facility location names | `'Pharmacy', 'Ward A Store'` |

---

## Query

```sql
SELECT
    DATE(sd.created_date) AS created_date,
    pk.name AS stock,
    org.name AS supplier_name,
    fl.name AS destination_location,
    SUM(sd.supplied_item_quantity) AS total_quantity,
    SUM(p.purchase_price * sd.supplied_item_quantity) AS total_purchase_price
FROM emr_supplydelivery sd
JOIN emr_deliveryorder delivery_order ON sd.order_id = delivery_order.id
JOIN emr_facilitylocation fl ON delivery_order.destination_id = fl.id
JOIN emr_organization org ON delivery_order.supplier_id = org.id
JOIN emr_inventoryitem ii ON sd.supplied_inventory_item_id = ii.id
JOIN emr_product p ON ii.product_id = p.id
JOIN emr_productknowledge pk ON p.product_knowledge_id = pk.id
WHERE delivery_order.supplier_id = 20697
  AND sd.deleted = FALSE
  AND delivery_order.deleted = FALSE
  AND fl.deleted = FALSE
  AND sd.status IN ('completed', 'in_progress')
  AND delivery_order.status IN ('completed', 'pending')
  AND fl.status = 'active'
  --[[AND {{created_date}}]]
  --[[AND fl.name IN ({{location}})]]
GROUP BY DATE(sd.created_date), org.name, fl.name, pk.name
ORDER BY DATE(sd.created_date) DESC, total_purchase_price DESC;
```



## Notes

- The supplier is hardcoded to `delivery_order.supplier_id = 20697` — update this to point to the relevant internal supplier organisation.
- Only non-deleted supply deliveries, delivery orders, and facility locations are included.
- Supply delivery status is filtered to `completed` and `in_progress`; delivery order status is filtered to `completed` and `pending` to capture both fulfilled and active orders.
- Only `active` destination locations are considered.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- Results are ordered by most recent date first, then by highest purchase value.

*Last updated: 2026-05-12*




