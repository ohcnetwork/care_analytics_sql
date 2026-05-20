
# X-Ray Revenue - SSMM

> Total revenue from X-ray charge items linked to issued/balanced invoices

## Purpose

Returns the total X-ray revenue at SSMM by summing `total_price` of charge items whose `charge_item_definition` belongs to the X-ray resource category (`category_id = 75`) and which are linked to a settled invoice.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `DATE` | DATE | Filter by date range (typically `inv.modified_date`) | `inv.modified_date BETWEEN '2026-05-01' AND '2026-05-04'` |

---

## Query

```sql
SELECT 
    COALESCE(SUM(ci.total_price), 0) AS total_revenue
FROM emr_chargeitem ci
JOIN emr_chargeitemdefinition cid ON ci.charge_item_definition_id = cid.id
JOIN emr_invoice inv ON ci.paid_invoice_id = inv.id
WHERE cid.category_id = 75
  AND inv.deleted = FALSE
  AND ci.status IN ('paid', 'billed')
  AND inv.status IN ('issued', 'balanced')
  --[[AND {{DATE}}]]

```


## Notes

- Hardcoded to `cid.category_id = 75` — the X-ray resource category. Update if this ID changes or new X-ray categories are added.
- `COALESCE(SUM(...), 0)` ensures the result is `0` instead of `NULL` when no rows match.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards

*Last updated: 2026-05-04*

````
