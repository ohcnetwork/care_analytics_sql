
# Total Stock Value Report - SSMM

> Net stock quantity and total purchase value per stock item, as of a given date.

## Purpose

Computes the current on-hand stock value for each stock item at SSMM as of a chosen date. It does this by:

1. Summing everything **purchased** (received via external supply deliveries) up to that date.
2. Subtracting everything **dispensed** to patients up to that date.
3. Subtracting **mistake adjustments** — stock moved into a configured set of "mistake / correction" destination locations, treated as outflow.

The result is the **net quantity** and **net purchase value** of stock remaining per item.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `selected_date` | DATE | As-of date for the report. All purchases, dispenses, and mistake entries up to and including this date are considered. | `'2026-05-31'` |

---

## Query

```sql
WITH purchase_items AS (
    SELECT 
        epk.name AS stock_name,
        SUM(esd.supplied_item_quantity) AS qty,
        SUM(ep.purchase_price * esd.supplied_item_quantity) AS total_value
    FROM emr_supplydelivery esd
    LEFT JOIN emr_deliveryorder edo ON esd.order_id = edo.id
    LEFT JOIN emr_product ep ON esd.supplied_item_id = ep.id
    LEFT JOIN emr_productknowledge epk ON ep.product_knowledge_id = epk.id
    WHERE esd.status = 'completed'
      AND edo.origin_id IS NULL
      AND esd.deleted = FALSE
      AND edo.deleted = FALSE
      AND edo.status = 'completed'
      AND ep.purchase_price IS NOT NULL
     --AND DATE(esd.created_date) <= {{selected_date}}
    GROUP BY epk.name
),

dispense_items AS (
    SELECT 
        epk.name AS stock_name,
        SUM(emd.quantity) AS qty,
        SUM(ep.purchase_price * emd.quantity) AS total_value
    FROM emr_medicationdispense emd
    LEFT JOIN emr_dispenseorder edo ON edo.id = emd.order_id
    LEFT JOIN emr_inventoryitem eii ON eii.id = emd.item_id
    LEFT JOIN emr_product ep ON eii.product_id = ep.id
    LEFT JOIN emr_productknowledge epk ON ep.product_knowledge_id = epk.id
    WHERE edo.status IN ('completed', 'in_progress', 'draft')
      AND emd.status IN ('completed', 'in_progress', 'preparation')
      AND emd.deleted = FALSE
      AND edo.deleted = FALSE
      AND ep.purchase_price IS NOT NULL
      --AND DATE(emd.created_date) <= {{selected_date}}
    GROUP BY epk.name
),

mistake_items AS (
    SELECT 
        epk.name AS stock_name,
        SUM(esd.supplied_item_quantity) AS qty,
        SUM(ep.purchase_price * esd.supplied_item_quantity) AS total_value
    FROM emr_supplydelivery esd
    LEFT JOIN emr_deliveryorder edo ON esd.order_id = edo.id
    LEFT JOIN emr_inventoryitem eii ON esd.supplied_inventory_item_id = eii.id
    LEFT JOIN emr_product ep ON eii.product_id = ep.id
    LEFT JOIN emr_productknowledge epk ON ep.product_knowledge_id = epk.id
    WHERE esd.status IN ('completed', 'in_progress')
      AND edo.destination_id IN (264,270,280,274,273,275,276,266,279,36,265,278,297,238,298,27,481,17,32,277)
      AND esd.deleted = FALSE
      AND edo.deleted = FALSE
      AND edo.status IN ('completed', 'in_progress')
      AND ep.purchase_price IS NOT NULL
      --AND DATE(esd.created_date) <= {{selected_date}}
    GROUP BY epk.name
)

SELECT 
    COALESCE(p.stock_name, d.stock_name, m.stock_name) AS stock_name,
    COALESCE(p.qty, 0) - COALESCE(d.qty, 0) - COALESCE(m.qty, 0) AS net_qty,
    COALESCE(p.total_value, 0) - COALESCE(d.total_value, 0) - COALESCE(m.total_value, 0) AS net_value
FROM purchase_items p
FULL OUTER JOIN dispense_items d ON p.stock_name = d.stock_name
FULL OUTER JOIN mistake_items m ON COALESCE(p.stock_name, d.stock_name) = m.stock_name
ORDER BY stock_name;
```


## Notes

- **`purchase_items` CTE** — external purchases only. Uses `edo.origin_id IS NULL` to filter to supply deliveries that originate from outside the facility
- **`dispense_items` CTE** — outflow via medication dispenses to patients. Includes dispense orders in `completed / in_progress / draft` and dispenses in `completed / in_progress / preparation` to match what reduces stock in practice.
- **`mistake_items` CTE** — supply deliveries whose destination is one of the configured "mistake / correction" locations. These represent stock moved out for adjustments and is treated as outflow.
- **Hardcoded values:**
  - `edo.destination_id IN (264,270,280,274,273,275,276,266,279,36,265,278,297,238,298,27,481,17,32,277)` — the list of "mistake / correction" destination locations. Update this list whenever new mistake/correction locations are added or old ones are retired.

*Last updated: 2026-05-22*



