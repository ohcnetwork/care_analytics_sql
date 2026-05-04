
# Lab Test Revenue - SSMM

> Total revenue from lab test charge items linked to issued/balanced invoices

## Purpose

Returns the total lab test revenue at SSMM by summing `total_price` of charge items whose `charge_item_definition` belongs to one of the lab test resource categories (`category_id IN (49, 50, 51, 52)`) and which are linked to a settled invoice.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `DATE` | DATE | Filter by date range (typically `inv.created_date` or `ci.created_date`) | `inv.created_date BETWEEN '2026-05-01' AND '2026-05-04'` |

---

## Query

```sql
SELECT 
    COALESCE(SUM(ci.total_price), 0) AS total_revenue_today
FROM emr_chargeitem ci
JOIN emr_chargeitemdefinition cid ON ci.charge_item_definition_id = cid.id
JOIN emr_resourcecategory rc ON cid.category_id = rc.id
JOIN emr_invoice inv ON ci.paid_invoice_id = inv.id
WHERE rc.id IN (49, 50, 51, 52)
  AND ci.deleted = FALSE
  AND inv.deleted = FALSE
  AND ci.status IN ('paid', 'billed')
  AND inv.status IN ('issued', 'balanced')
  --[[AND {{DATE}}]]
;
```


## Notes

- Hardcoded to `rc.id IN (49, 50, 51, 52)` — the lab test resource categories. Update if these IDs change or new lab categories are added.
- `COALESCE(SUM(...), 0)` ensures the result is `0` instead of `NULL` when no rows match.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.

*Last updated: 2026-05-04*

````
