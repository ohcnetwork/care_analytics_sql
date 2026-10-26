# External Purchase Value - SSMM

> Net supplier purchase value for the current financial year up to a selected date, excluding supplier 20697

## Purpose

Calculates the value of stock purchased from external suppliers between the start of the financial year (1 April 2026) and the selected date. It starts from total supplier purchases, removes the value moved into error locations, and then removes purchases from supplier `20697`.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `selected_date` | date | **Required.** Upper bound (inclusive) for delivery `created_date` | `2026-09-30` |

---

## Query

```sql
WITH total_purchases AS (
    SELECT SUM(purchase_price * supplied_item_quantity) AS sum
    FROM emr_supplydelivery esd
    LEFT JOIN emr_deliveryorder edo ON esd.order_id = edo.id
    LEFT JOIN emr_product ep ON esd.supplied_item_id = ep.id
    WHERE esd.status = 'completed'
      AND edo.origin_id IS NULL
      AND edo.supplier_id IS NOT NULL
      AND esd.deleted = FALSE
      AND edo.deleted = FALSE
      AND purchase_price IS NOT NULL
      AND DATE(esd.created_date) >= DATE '2026-04-01'
      AND DATE(esd.created_date) <= {{selected_date}}
),

total_error AS (
    SELECT SUM(purchase_price * supplied_item_quantity) AS sum
    FROM emr_supplydelivery esd
    LEFT JOIN emr_deliveryorder edo ON esd.order_id = edo.id
    LEFT JOIN emr_inventoryitem eii ON esd.supplied_inventory_item_id = eii.id
    LEFT JOIN emr_product ep ON eii.product_id = ep.id
    WHERE esd.status IN ('completed', 'in_progress')
      AND edo.destination_id IN (264, 636)
      AND edo.id != 5724
      AND esd.deleted = FALSE
      AND edo.deleted = FALSE
      AND purchase_price IS NOT NULL
      AND DATE(esd.created_date) >= DATE '2026-04-01'
      AND DATE(esd.created_date) <= {{selected_date}}
),

supplier_20697 AS (
    SELECT SUM(purchase_price * supplied_item_quantity) AS sum
    FROM emr_supplydelivery esd
    LEFT JOIN emr_deliveryorder edo ON esd.order_id = edo.id
    LEFT JOIN emr_product ep ON esd.supplied_item_id = ep.id
    WHERE esd.status = 'completed'
      AND edo.origin_id IS NULL
      AND edo.supplier_id = '20697'
      AND esd.deleted = FALSE
      AND edo.deleted = FALSE
      AND purchase_price IS NOT NULL
      AND DATE(esd.created_date) >= DATE '2026-04-01'
      AND DATE(esd.created_date) <= {{selected_date}}
)

SELECT
    CASE
        WHEN {{selected_date}} < DATE '2026-04-01' THEN NULL
        ELSE (COALESCE(tp.sum, 0) - COALESCE(er.sum, 0)) - COALESCE(sp.sum, 0)
    END AS result
FROM total_purchases tp, total_error er, supplier_20697 sp;
```

## Notes

- **Formula:** `result = supplier purchases − value moved to error locations − purchases from supplier 20697`, all from 1 April 2026 to `selected_date`.
- **Error deduction (`total_error`):** Completed or in-progress deliveries into locations `264` and `636`, valued through `supplied_inventory_item_id`. 
- **Supplier 20697 deduction (`supplier_20697`):** Completed purchases from supplier `20697`, removed so the result reflects other (external) suppliers only.
- **Hardcoded values:** Financial year start `2026-04-01` (four places), location ids `264`, `636`, order id `5724`, and supplier id `20697`.
- **Before the financial year:** If `selected_date` is earlier than 1 April 2026, the result is `NULL`.
- **Required variable:** `selected_date` is not wrapped in optional `[[...]]` brackets, so the query needs a value to return a meaningful total.
- Output is a single row with one value in the `result` column.

*Last updated: 2026-10-13*
