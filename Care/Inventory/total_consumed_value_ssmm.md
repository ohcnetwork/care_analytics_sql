# Total Consumed Value - SSMM

> Net value of stock moved into consumption locations for the current financial year up to a selected date

## Purpose

Calculates the total value of stock consumed between the start of the financial year (1 April 2026) and the selected date. Consumption is measured as the value of stock delivered into consumption locations minus the value of stock sent back out of them.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `selected_date` | date | **Required.** Upper bound (inclusive) for delivery `created_date` | `2026-09-30` |

---

## Query

```sql
SELECT
    CASE
        WHEN {{selected_date}} < DATE '2026-04-01' THEN NULL
        ELSE COALESCE(SUM(ep.purchase_price * esd.supplied_item_quantity)
                 FILTER (WHERE edo.destination_id IN (270, 280, 274, 273, 275, 276, 266, 279, 36, 265, 278, 297, 238, 298, 27, 481, 17, 32, 277)), 0)
           - COALESCE(SUM(ep.purchase_price * esd.supplied_item_quantity)
                 FILTER (WHERE edo.origin_id IN (270, 280, 274, 273, 275, 276, 266, 279, 36, 265, 278, 297, 238, 298, 27, 481, 17, 32, 277)), 0)
    END AS total_consumed
FROM emr_supplydelivery esd
JOIN emr_deliveryorder edo ON edo.id = esd.order_id
JOIN emr_inventoryitem eii ON eii.id = esd.supplied_inventory_item_id
JOIN emr_product ep ON ep.id = eii.product_id
WHERE esd.status IN ('completed', 'in_progress')
  AND esd.deleted = FALSE
  AND edo.deleted = FALSE
  AND ep.purchase_price IS NOT NULL
  AND DATE(esd.created_date) >= DATE '2026-04-01'
  AND DATE(esd.created_date) <= {{selected_date}};
```

## Notes

- **Formula:** `total_consumed = value delivered into consumption locations − value sent out of consumption locations`, from 1 April 2026 to `selected_date`.
- **Valuation:** Each delivery is valued at `purchase_price × supplied_item_quantity`, using the product linked through `supplied_inventory_item_id`.
- **In-progress deliveries:** Both `completed` and `in_progress` deliveries are counted, so stock is treated as consumed once it is dispatched, not only when received.
- **Hardcoded location list:** The 19 consumption location ids appear twice (destination and origin filters). Keep both lists identical when adding or removing a location.
- **Hardcoded financial year:** The start date `2026-04-01` is fixed in two places; update both when the financial year changes.
- **Before the financial year:** If `selected_date` is earlier than 1 April 2026, the result is `NULL`.
- Output is a single row with one value.

*Last updated: 2026-10-13*
