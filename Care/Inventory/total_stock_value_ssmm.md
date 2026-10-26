# Total Stock Value - SSMM

> Value of stock on hand as of a selected date, at purchase cost

## Purpose

Estimates the total value of stock held as of the selected date by taking everything brought into inventory and subtracting what was dispensed and what was moved into consumption or error locations. 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `selected_date` | date | **Required.** Upper bound (inclusive) for `created_date` in all three parts | `2026-09-30` |

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
          AND edo.origin_id IS NULL
          AND edo.destination_id NOT IN (36)
          AND esd.deleted = FALSE
          AND edo.deleted = FALSE
          AND purchase_price IS NOT NULL
          AND DATE(esd.created_date) <= {{selected_date}}
    ) t
),

dispenses AS (
    SELECT SUM(total_purchase_price) AS sum
    FROM (
        SELECT (purchase_price * emd.quantity) AS total_purchase_price
        FROM emr_medicationdispense emd
        LEFT JOIN emr_dispenseorder edo ON edo.id = emd.order_id
        LEFT JOIN emr_inventoryitem eii ON eii.id = emd.item_id
        LEFT JOIN emr_product ep ON eii.product_id = ep.id
        LEFT JOIN emr_chargeitem eci ON emd.charge_item_id = eci.id
        WHERE emd.status NOT IN ('cancelled', 'entered_in_error', 'stopped', 'declined')
          AND emd.deleted = FALSE
          AND edo.deleted = FALSE
          AND DATE(emd.created_date) <= {{selected_date}}
          AND purchase_price IS NOT NULL
    ) t
),

mistakes AS (
    SELECT
          coalesce(sum(ep.purchase_price * esd.supplied_item_quantity)
            filter (where edo.destination_id in (264,270,280,274,273,275,276,266,279,36,265,278,297,238,298,27,481,17,32,277,636)),0)
      - coalesce (sum(ep.purchase_price * esd.supplied_item_quantity)
            filter (where edo.origin_id in (264,270,280,274,273,275,276,266,279,36,265,278,297,238,298,27,481,17,32,277,636)),0)
            as sum
    FROM emr_supplydelivery esd
    JOIN emr_deliveryorder edo ON edo.id = esd.order_id
    JOIN emr_inventoryitem eii ON eii.id = esd.supplied_inventory_item_id
    JOIN emr_product ep ON ep.id = eii.product_id
    WHERE esd.status IN ('completed', 'in_progress')
      AND esd.deleted = FALSE
      AND edo.deleted = FALSE
      AND ep.purchase_price IS NOT NULL
      AND DATE(esd.created_date) <= {{selected_date}}
)

SELECT
    CASE
        WHEN {{selected_date}} < DATE '2026-04-01' THEN NULL
        ELSE COALESCE(tp.sum, 0) - COALESCE(d.sum, 0) - COALESCE(m.sum, 0)
    END AS total_stock_value
FROM total_purchases tp, dispenses d, mistakes m;
```

## Notes

- **Formula:** `total_stock_value = stock brought in − dispensed − net moved to consumption/error locations`, all at purchase cost and up to `selected_date`.
- **All-time totals:** Unlike the purchase, consumed, dispensed, and return reports, there is no 1 April 2026 lower bound. Every part is cumulative from the start of the data up to `selected_date`..
- **Hardcoded location list:** The 21 location ids appear twice in `mistakes`; keep both lists identical.
- **Before the financial year:** If `selected_date` is earlier than 1 April 2026, the result is `NULL`, even though the query itself has no financial-year lower bound.
- **Required variable:** `selected_date` is not wrapped in optional `[[...]]` brackets, so the query needs a value to return a meaningful total.
- Output is a single row with one value.

*Last updated: 2026-10-13*
