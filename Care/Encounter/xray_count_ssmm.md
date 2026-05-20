
# X-Ray Count - SSMM

> Total count of X-ray charge items (in the X-ray resource category)

## Purpose

Returns the total number of X-rays at SSMM by counting charge items whose `charge_item_definition` belongs to the X-ray resource category (`category_id = 75`) 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `DATE` | DATE | Filter by date range (typically `ci.modified_date`) | `ci.modified_date BETWEEN '2026-05-01' AND '2026-05-04'` |

---

## Query

```sql
SELECT 
    COUNT(ci.id) AS total_tests
FROM emr_chargeitem ci
JOIN emr_chargeitemdefinition cid ON ci.charge_item_definition_id = cid.id
WHERE cid.category_id = 75
  AND ci.status IN ('paid', 'billed', 'billable')
  --[[AND {{DATE}}]]

```



## Notes

- Hardcoded to `cid.category_id = 75` — the X-ray resource category. Update if this category ID changes or new X-ray categories are added.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards

*Last updated: 2026-05-04*

````
