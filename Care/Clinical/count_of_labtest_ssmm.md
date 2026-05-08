
# Lab Test Count - SSMM

> Total count of lab test charge items

## Purpose

Returns the total number of lab tests at SSMM by counting charge items whose `charge_item_definition` belongs to one of the lab test resource categories (`category_id IN (49, 50, 51, 52)`) 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `DATE` | DATE | Filter by date range (typically `ci.created_date`) | `ci.created_date BETWEEN '2026-05-01' AND '2026-05-04'` |

---

## Query

```sql
SELECT 
    COUNT(ci.id) AS total_tests
FROM emr_chargeitem ci
JOIN emr_chargeitemdefinition cid ON ci.charge_item_definition_id = cid.id
JOIN emr_resourcecategory rc ON cid.category_id = rc.id
WHERE rc.id IN (49, 50, 51, 52)
  AND ci.deleted = FALSE
  AND ci.status IN ('paid', 'billed', 'billable')
  --[[AND {{DATE}}]]
;
```

## Notes

- Hardcoded to `rc.id IN (49, 50, 51, 52)` — the lab test resource categories. Update if these category IDs change or new lab categories are added.
- Only active (`ci.deleted = FALSE`) charge items are included.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards

*Last updated: 2026-05-04*

````
