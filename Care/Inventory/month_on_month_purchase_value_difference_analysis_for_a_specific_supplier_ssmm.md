# Month on Month Purchase Value Difference Analysis for a Specific Supplier - SSMM

> Completed supplier deliveries with product value, location, and creator details

## Purpose

Lists completed supply deliveries for a single supplier and shows the purchase value at product level.


## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `start_date` | date | Optional lower bound for `created_date` | `2026-01-01` |
| `end_date` | date | Optional upper bound for `created_date` | `2026-01-31` |

---

## Query

```sql
SELECT
	epk.name AS product_name,
	esd.supplied_item_quantity AS quantity,
	ep.purchase_price AS unit_price,
	(ep.purchase_price * esd.supplied_item_quantity) AS value,
	DATE(esd.created_date) AS created_date,
	org.name AS supplier_name,
	fl.name AS destination_location,
	CONCAT(u.first_name, ' ', u.last_name) AS created_by
FROM emr_supplydelivery esd
JOIN emr_deliveryorder edo
	ON esd.order_id = edo.id
JOIN emr_product ep
	ON esd.supplied_item_id = ep.id
JOIN emr_productknowledge epk
	ON epk.id = ep.product_knowledge_id
JOIN users_user u
	ON u.id = edo.created_by_id
JOIN emr_organization org
	ON org.id = edo.supplier_id
JOIN emr_facilitylocation fl
	ON fl.id = edo.destination_id
WHERE esd.status = 'completed'
  AND edo.origin_id IS NULL
  AND edo.supplier_id = 20697
  AND edo.status = 'completed'
  AND ep.purchase_price IS NOT NULL
  --AND ({{start_date}} IS NULL OR DATE(esd.created_date) > {{start_date}}::date)
  --AND ({{end_date}} IS NULL OR DATE(esd.created_date) <= {{end_date}}::date)
ORDER BY value DESC;
```

## Notes

- **Supplier filter:** `edo.supplier_id = '20697'` is hardcoded, so the query is scoped to one supplier.
- **Completed deliveries only:** Both `esd.status` and `edo.status` must be `completed`.
- **Ordering:** Results are sorted by highest purchase value first.


*Last updated: 2026-08-31*
