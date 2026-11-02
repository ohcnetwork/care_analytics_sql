# Stock Report by Location - SSMM

> Quantity and purchase-cost value of stock on hand per product and storage location as of a selected date

## Purpose

Builds a running stock ledger from every purchase, dispense, transfer, and move into/out of consumption locations up to the selected date, then shows the remaining quantity and value for each product at each storage location. Useful for location-level stock checks and for spotting negative or mismatched stock.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `selected_date` | date | **Required.** Upper bound (inclusive) for `created_date` in every movement | `2026-09-30` |

---

## Query

```sql
WITH ex AS (
    SELECT ARRAY[
        264, 270, 280, 274, 273, 275, 276, 266, 279, 36, 265, 278, 297,
        238, 298, 27, 481, 17, 32, 277, 636, 638, 639, 641
    ] AS ids
),

movements AS (

    -- PURCHASES: stock from outside, credited to destination
    SELECT
        ep.id AS product_id,
        edo.destination_id AS location_id,
        ep.purchase_price * esd.supplied_item_quantity AS purchase_value,
        esd.supplied_item_quantity AS purchase_qty,
        0 AS dispense_value, 0 AS dispense_qty,
        0 AS mistake_value, 0 AS mistake_qty
    FROM emr_supplydelivery esd
    LEFT JOIN emr_deliveryorder edo ON esd.order_id = edo.id
    LEFT JOIN emr_product ep ON esd.supplied_item_id = ep.id
    WHERE esd.status = 'completed'
      AND edo.origin_id IS NULL
      AND esd.deleted = FALSE
      AND edo.deleted = FALSE
      AND ep.purchase_price IS NOT NULL
      AND DATE(esd.created_date) <= {{selected_date}}

    UNION ALL

    -- DISPENSES: debited to the item's location; consumption locations become NULL = "(no location)"
    SELECT
        ep.id,
        CASE WHEN eii.location_id = ANY(ex.ids) THEN NULL ELSE eii.location_id END,
        0, 0,
        ep.purchase_price * emd.quantity, emd.quantity,
        0, 0
    FROM emr_medicationdispense emd
    LEFT JOIN emr_dispenseorder edo ON edo.id = emd.order_id
    LEFT JOIN emr_inventoryitem eii ON eii.id = emd.item_id
    LEFT JOIN emr_product ep ON eii.product_id = ep.id
    CROSS JOIN ex
    WHERE emd.status NOT IN ('cancelled', 'entered_in_error', 'stopped', 'declined')
      AND emd.deleted = FALSE
      AND edo.deleted = FALSE
      AND ep.purchase_price IS NOT NULL
      AND DATE(emd.created_date) <= {{selected_date}}

    UNION ALL

    -- MISTAKES IN: into a consumption location, charged to the origin
    -- (a supplier delivery has no origin, so it nets against its purchase at the destination)
    SELECT
        ep.id,
        COALESCE(edo.origin_id, edo.destination_id),
        0, 0, 0, 0,
        ep.purchase_price * esd.supplied_item_quantity,
        esd.supplied_item_quantity
    FROM emr_supplydelivery esd
    JOIN emr_deliveryorder edo ON edo.id = esd.order_id
    JOIN emr_inventoryitem eii ON eii.id = esd.supplied_inventory_item_id
    JOIN emr_product ep ON ep.id = eii.product_id
    CROSS JOIN ex
    WHERE esd.status IN ('completed', 'in_progress')
      AND esd.deleted = FALSE
      AND edo.deleted = FALSE
      AND ep.purchase_price IS NOT NULL
      AND DATE(esd.created_date) <= {{selected_date}}
      AND edo.destination_id = ANY(ex.ids)

    UNION ALL

    -- MISTAKES OUT: out of a consumption location, credited to the destination
    SELECT
        ep.id,
        edo.destination_id,
        0, 0, 0, 0,
        -(ep.purchase_price * esd.supplied_item_quantity),
        -esd.supplied_item_quantity
    FROM emr_supplydelivery esd
    JOIN emr_deliveryorder edo ON edo.id = esd.order_id
    JOIN emr_inventoryitem eii ON eii.id = esd.supplied_inventory_item_id
    JOIN emr_product ep ON ep.id = eii.product_id
    CROSS JOIN ex
    WHERE esd.status IN ('completed', 'in_progress')
      AND esd.deleted = FALSE
      AND edo.deleted = FALSE
      AND ep.purchase_price IS NOT NULL
      AND DATE(esd.created_date) <= {{selected_date}}
      AND edo.origin_id = ANY(ex.ids)

    UNION ALL

    -- TRANSFER IN: storage to storage, credited to destination
    SELECT
        ep.id,
        edo.destination_id,
        ep.purchase_price * esd.supplied_item_quantity,
        esd.supplied_item_quantity,
        0, 0, 0, 0
    FROM emr_supplydelivery esd
    JOIN emr_deliveryorder edo ON edo.id = esd.order_id
    JOIN emr_inventoryitem eii ON eii.id = esd.supplied_inventory_item_id
    JOIN emr_product ep ON ep.id = eii.product_id
    CROSS JOIN ex
    WHERE esd.status IN ('completed', 'in_progress')
      AND esd.deleted = FALSE
      AND edo.deleted = FALSE
      AND ep.purchase_price IS NOT NULL
      AND DATE(esd.created_date) <= {{selected_date}}
      AND edo.origin_id IS NOT NULL
      AND edo.origin_id <> ALL(ex.ids)
      AND edo.destination_id <> ALL(ex.ids)

    UNION ALL

    -- TRANSFER OUT: same rows, debited to origin
    SELECT
        ep.id,
        edo.origin_id,
        0, 0,
        ep.purchase_price * esd.supplied_item_quantity,
        esd.supplied_item_quantity,
        0, 0
    FROM emr_supplydelivery esd
    JOIN emr_deliveryorder edo ON edo.id = esd.order_id
    JOIN emr_inventoryitem eii ON eii.id = esd.supplied_inventory_item_id
    JOIN emr_product ep ON ep.id = eii.product_id
    CROSS JOIN ex
    WHERE esd.status IN ('completed', 'in_progress')
      AND esd.deleted = FALSE
      AND edo.deleted = FALSE
      AND ep.purchase_price IS NOT NULL
      AND DATE(esd.created_date) <= {{selected_date}}
      AND edo.origin_id IS NOT NULL
      AND edo.origin_id <> ALL(ex.ids)
      AND edo.destination_id <> ALL(ex.ids)
)

SELECT
    REPLACE(epk.name, 'Internal Stock Update ', '') AS name,
    fl.name AS location,
    SUM(m.purchase_qty) - SUM(m.dispense_qty) - SUM(m.mistake_qty) AS total_qty,
    SUM(m.purchase_value) - SUM(m.dispense_value) - SUM(m.mistake_value) AS stock_value
FROM movements m
JOIN emr_product ep ON ep.id = m.product_id
LEFT JOIN emr_productknowledge epk ON epk.id = ep.product_knowledge_id
LEFT JOIN emr_facilitylocation fl ON fl.id = m.location_id
CROSS JOIN ex
WHERE m.location_id IS NULL OR m.location_id <> ALL(ex.ids)
GROUP BY REPLACE(epk.name, 'Internal Stock Update ', ''), fl.id, fl.name
HAVING SUM(m.purchase_value) - SUM(m.dispense_value) - SUM(m.mistake_value) <> 0
    OR SUM(m.purchase_qty) - SUM(m.dispense_qty) - SUM(m.mistake_qty) <> 0
ORDER BY stock_value;
```

## Notes

- **Formula per product and location:** `stock = purchases + transfers in − dispenses − transfers out − net moves into consumption/error locations`. Transfers in are added to the purchase columns and transfers out to the dispense columns.
- **Excluded locations (`ex`):** 24 consumption and error location ids. They are never shown as a location in the output; stock that reaches them is treated as used up.

### Movement types

| Movement | Location charged | Effect | Statuses |
|----------|------------------|--------|----------|
| Purchase (no origin) | Destination | `+` | `completed` |
| Dispense | Inventory item's location | `−` | All except cancelled, entered-in-error, stopped, declined |
| Mistake in (to an excluded location) | Origin, or destination if there is no origin | `−` | `completed`, `in_progress` |
| Mistake out (from an excluded location) | Destination | `+` (negative mistake) | `completed`, `in_progress` |
| Transfer in (storage → storage) | Destination | `+` | `completed`, `in_progress` |
| Transfer out (storage → storage) | Origin | `−` | `completed`, `in_progress` |

- **In-progress transfers:** Transfers that are still `in_progress` are already moved from origin to destination, so stock is counted at the destination before it is received.
- **Purchases include patient returns:** Purchases only require `origin_id IS NULL`, with no `supplier_id` filter, so patient medication returns are added back as stock at their destination. 
- **All-time totals:** Every movement up to `selected_date` is included.
- **Hardcoded location list:** Update the `ex` array when consumption or error locations change.
- **Required variable:** `selected_date` is not wrapped in optional `[[...]]` brackets, so the query needs a value to run.

*Last updated: 2026-10-30*
