
# Items Transferred to Consumption and Entered-in-Error Locations

> Summary of stock transferred into a curated set of consumption / entered in error destination locations, with value

## Purpose

Summarises supply deliveries at SSMM whose **destination** is one of a curated list of "consumption" or "entered in error" facility locations. Groups by day, origin, destination, and both delivery statuses, reporting total quantity and total purchase-price value moved. 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created_date` | DATE / range | Metabase date filter (typically bound to `sd.created_date`) | `'2026-07-01'` |
| `location` | TEXT (multi) | Filter by one or more origin location names | `'Pharmacy', 'Main Store'` |

---

## Query

```sql
SELECT
    DATE(sd.created_date) AS created_date,
    fl_origin.name AS origin_location,
    fl_destination.name AS destination_location,
    sd.status,
    delivery_order.status,
    SUM(sd.supplied_item_quantity) AS total_quantity,
    SUM(p.purchase_price * sd.supplied_item_quantity) AS total_purchase_price
FROM emr_supplydelivery sd
JOIN emr_deliveryorder delivery_order
    ON sd.order_id = delivery_order.id
JOIN emr_facilitylocation fl_destination
    ON delivery_order.destination_id = fl_destination.id
JOIN emr_facilitylocation fl_origin
    ON delivery_order.origin_id = fl_origin.id
JOIN emr_inventoryitem ii
    ON sd.supplied_inventory_item_id = ii.id
JOIN emr_product p
    ON ii.product_id = p.id
WHERE fl_destination.id IN (
    264, 32, 280, 266, 36, 638, 279, 278, 265, 481, 27, 298,
    17, 273, 639, 275, 238, 270, 276, 274, 277, 297, 641
)
  AND fl_destination.deleted = FALSE
  AND fl_origin.deleted = FALSE
  AND sd.status IN ('completed', 'in_progress')
  AND delivery_order.status IN ('completed', 'pending')
  AND fl_destination.status = 'active'
  AND fl_origin.status = 'active'
  --[[AND {{created_date}}]]
  --[[AND fl_origin.name IN ({{location}})]]
GROUP BY DATE(sd.created_date), fl_origin.name, fl_destination.name, sd.status, delivery_order.status
ORDER BY DATE(sd.created_date) DESC, total_purchase_price DESC;
```

## Notes
- **Metabase filters:**
  - `[[AND {{created_date}}]]` is a field filter — bind it to `sd.created_date`.
  - `[[AND fl_origin.name IN ({{location}})]]` — multi-select filter on origin location name.
- Results are ordered by most recent date first, then by highest purchase value within each day.

*Last updated: 2026-07-24*
