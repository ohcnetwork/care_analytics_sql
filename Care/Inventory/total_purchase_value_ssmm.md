# Total Purchase Value - SSMM

> Net supplier purchase value for the current financial year up to a selected date

## Purpose

Calculates the total value of stock purchased from suppliers between the start of the financial year (1 April 2026) and the selected date, minus the value of stock moved into error locations in the same period.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `selected_date` | date | **Required.** Upper bound (inclusive) for delivery `created_date` | `2026-09-30` |

---

## Query

```sql
WITH total_purchases AS (
    SELECT SUM(total_purchase_price) AS sum
    FROM (
        SELECT (purchase_price * supplied_item_quantity) AS total_purchase_price
        FROM emr_supplydelivery esd
        LEFT JOIN emr_deliveryorder edo ON esd.order_id = edo.id
        LEFT JOIN emr_product ep ON esd.supplied_item_id = ep.id
        WHERE esd.status = 'completed'
          AND edo.destination_id NOT IN (36)
          AND edo.origin_id IS NULL
          AND edo.supplier_id IS NOT NULL
          AND esd.deleted = FALSE
          AND edo.deleted = FALSE
          AND purchase_price IS NOT NULL
          AND DATE(esd.created_date) >= DATE '2026-04-01'
          AND DATE(esd.created_date) <= {{selected_date}}
    ) t
),

total_error AS (
    SELECT COALESCE(SUM(ep.purchase_price * esd.supplied_item_quantity), 0) AS sum
    FROM emr_supplydelivery esd
    JOIN emr_deliveryorder edo ON esd.order_id = edo.id
    JOIN emr_inventoryitem eii ON esd.supplied_inventory_item_id = eii.id
    JOIN emr_product ep ON eii.product_id = ep.id
    WHERE esd.status IN ('completed', 'in_progress')
      AND edo.destination_id IN (264, 636)
      AND esd.deleted = FALSE
      AND edo.deleted = FALSE
      AND ep.purchase_price IS NOT NULL
      AND DATE(esd.created_date) >= DATE '2026-04-01'
      AND DATE(esd.created_date) <= {{selected_date}}
)

SELECT
    CASE
        WHEN {{selected_date}} < DATE '2026-04-01' THEN NULL
        ELSE COALESCE(tp.sum, 0) - COALESCE(er.sum, 0)
    END AS total_purchase
FROM total_purchases tp, total_error er;
```

## Notes

- **Formula:** `total_purchase = supplier purchases − value moved to error locations`, both from 1 April 2026 to `selected_date`.
- **Supplier purchases (`total_purchases`):** Completed deliveries from an external supplier (`supplier_id IS NOT NULL`, `origin_id IS NULL`), excluding deliveries to location `36`. Value is `purchase_price × supplied_item_quantity`, with price taken from the product linked through `supplied_item_id`.
- **Error deduction (`total_error`):** Completed or in-progress deliveries into locations `264` and `636`, valued using the product linked through `supplied_inventory_item_id`. This covers any delivery into those locations, including internal transfers, not just supplier deliveries.
- **Hardcoded financial year:** The start date `2026-04-01` is fixed in three places; update all of them when the financial year changes.
- **Before the financial year:** If `selected_date` is earlier than 1 April 2026, the result is `NULL`.
- **Hardcoded location ids:** `36`, `264`, and `636` are SSMM-specific location ids.

*Last updated: 2026-10-13*
