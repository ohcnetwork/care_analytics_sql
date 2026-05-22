
# Scan Count - SSMM

> Total count of scans charge items (in the scan resource categories)

## Purpose

Returns the total number of scans (e.g. ultrasound, CT, MRI etc.) at SSMM by counting charge items whose `charge_item_definition` belongs to one of the scan resource categories (`category_id IN (32, 57)`) 

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
WHERE cid.category_id IN (32,57)
  AND ci.status IN ('paid', 'billed', 'billable')
  --[[AND {{DATE}}]]
;
```



## Notes

- Hardcoded to `cid.category_id  IN (32, 57)` — the scan / imaging resource categories. Update if these category IDs change or new scan categories are added.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.

*Last updated: 2026-05-04*

````
