
# Total Stock Value with Location Split - SSMM

> Product-wise stock balance and valuation at a location, split by incoming, outgoing (normal/error), and dispensed quantities

## Purpose

Computes stock per product for a selected location/date by combining completed incoming supplies, outgoing transfers (split into normal vs entered-in-error/consumption destinations), and medication dispenses. Also calculates total stock value using purchase price.


## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `selected_date` | DATE | Snapshot cutoff date (includes all transactions up to this date) | `'2026-08-01'` |
| `location_id` | INTEGER | Facility location id to compute stock for | `239` |

---

## Query

```sql
SELECT
		REPLACE(epk.name, 'Internal Stock Update ', '') AS name,
		SUM(total) AS total,
		SUM(incoming_count) AS incoming_count,
		SUM(outgoing_normal_count) AS outgoing_normal_count,
		SUM(outgoing_error_count) AS outgoing_error_count,
		SUM(dispense_count) AS dispense_count,
		SUM(ep.purchase_price * total) AS total_price
FROM (
		SELECT
				COALESCE(incoming.id, outgoing_normal.id, outgoing_error.id, dispenses.id) AS final_id,
				(COALESCE(incoming.count, 0) - COALESCE(outgoing_normal.count, 0) - COALESCE(outgoing_error.count, 0) - COALESCE(dispenses.count, 0)) AS total,
				incoming.count AS incoming_count,
				outgoing_normal.count AS outgoing_normal_count,
				outgoing_error.count AS outgoing_error_count,
				dispenses.count AS dispense_count
		FROM (
				SELECT id, SUM(count) AS count
				FROM (
						SELECT
								COALESCE(id_nn, COALESCE(id, id_n)) AS id,
								(COALESCE(count, 0) + COALESCE(count_n, 0) + COALESCE(count_nn, 0)) AS count
						FROM (
								SELECT ep.id AS id, SUM(supplied_item_quantity) AS count
								FROM emr_supplydelivery esd
								LEFT JOIN emr_deliveryorder edo ON esd.order_id = edo.id
								LEFT JOIN emr_inventoryitem eii ON esd.supplied_inventory_item_id = eii.id
								LEFT JOIN emr_product ep ON eii.product_id = ep.id
								WHERE esd.status = 'completed'
									AND esd.deleted = FALSE AND edo.deleted = FALSE
									AND DATE(esd.created_date) <= {{selected_date}}
									AND destination_id = {{location_id}}
									AND supplied_item_id IS NULL
									AND supplied_inventory_item_id IS NOT NULL
								GROUP BY ep.id
						) supplied_inventory_item_only
						FULL OUTER JOIN (
								SELECT supplied_item_id AS id_n, SUM(supplied_item_quantity) AS count_n
								FROM emr_supplydelivery esd
								LEFT JOIN emr_deliveryorder edo ON esd.order_id = edo.id
								WHERE esd.status = 'completed'
									AND esd.deleted = FALSE AND edo.deleted = FALSE
									AND DATE(esd.created_date) <= {{selected_date}}
									AND destination_id = {{location_id}}
									AND supplied_inventory_item_id IS NULL
									AND supplied_item_id IS NOT NULL
								GROUP BY supplied_item_id
						) supplied_item_only ON supplied_inventory_item_only.id = supplied_item_only.id_n
						FULL OUTER JOIN (
								SELECT supplied_item_id AS id_nn, SUM(supplied_item_quantity) AS count_nn
								FROM emr_supplydelivery esd
								LEFT JOIN emr_deliveryorder edo ON esd.order_id = edo.id
								WHERE supplied_inventory_item_id IS NOT NULL
									AND supplied_item_id IS NOT NULL
									AND esd.status = 'completed'
									AND esd.deleted = FALSE AND edo.deleted = FALSE
									AND DATE(esd.created_date) <= {{selected_date}}
									AND destination_id = {{location_id}}
								GROUP BY supplied_item_id
						) all_supplied_item ON all_supplied_item.id_nn = supplied_item_only.id_n
				) combined
				GROUP BY id
		) incoming

		FULL OUTER JOIN (
				SELECT ep.id AS id, SUM(supplied_item_quantity) AS count
				FROM emr_supplydelivery esd
				LEFT JOIN emr_deliveryorder edo ON esd.order_id = edo.id
				LEFT JOIN emr_inventoryitem eii ON esd.supplied_inventory_item_id = eii.id
				LEFT JOIN emr_product ep ON eii.product_id = ep.id
				WHERE esd.status IN ('completed', 'in_progress')
					AND esd.deleted = FALSE AND edo.deleted = FALSE
					AND DATE(esd.created_date) <= {{selected_date}}
					AND origin_id = {{location_id}}
					AND destination_id NOT IN (264, 270, 280, 274, 273, 275, 276, 266, 279, 36, 265, 278, 297, 238, 298, 27, 481, 17, 32, 277)
				GROUP BY ep.id
		) outgoing_normal ON incoming.id = outgoing_normal.id

		FULL OUTER JOIN (
				SELECT ep.id AS id, SUM(supplied_item_quantity) AS count
				FROM emr_supplydelivery esd
				LEFT JOIN emr_deliveryorder edo ON esd.order_id = edo.id
				LEFT JOIN emr_inventoryitem eii ON esd.supplied_inventory_item_id = eii.id
				LEFT JOIN emr_product ep ON eii.product_id = ep.id
				WHERE esd.status IN ('completed', 'in_progress')
					AND esd.deleted = FALSE AND edo.deleted = FALSE
					AND DATE(esd.created_date) <= {{selected_date}}
					AND origin_id = {{location_id}}
					AND destination_id IN (264, 270, 280, 274, 273, 275, 276, 266, 279, 36, 265, 278, 297, 238, 298, 27, 481, 17, 32, 277)
				GROUP BY ep.id
		) outgoing_error ON COALESCE(incoming.id, outgoing_normal.id) = outgoing_error.id

		FULL OUTER JOIN (
				SELECT ep.id AS id, SUM(emd.quantity) AS count
				FROM emr_medicationdispense emd
				LEFT JOIN emr_inventoryitem eii ON eii.id = emd.item_id
				LEFT JOIN emr_product ep ON eii.product_id = ep.id
				WHERE emd.status NOT IN ('cancelled', 'entered_in_error', 'stopped', 'declined')
					AND emd.deleted = FALSE
					AND DATE(emd.created_date) <= {{selected_date}}
					AND eii.location_id = {{location_id}}
				GROUP BY ep.id
		) dispenses ON COALESCE(incoming.id, outgoing_normal.id, outgoing_error.id) = dispenses.id
) total
LEFT JOIN emr_product ep ON ep.id = total.final_id
LEFT JOIN emr_productknowledge epk ON epk.id = ep.product_knowledge_id
WHERE total.total > 0
GROUP BY REPLACE(epk.name, 'Internal Stock Update ', '')
ORDER BY SUM(total);
```

## Notes

- Stock balance formula per item: `incoming - outgoing_normal - outgoing_error - dispensed`.
- Filters to positive balance only (`WHERE total.total > 0`).
- Both `selected_date` and `location_id` are required variables.
- The hard coded destination id's refer to the entered in error and consumption locations, update if needed

*Last updated: 2026-08-13*
