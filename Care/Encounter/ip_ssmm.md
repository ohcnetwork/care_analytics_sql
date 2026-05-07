
# IP Encounter Count - SSMM (Excluding Fake Beds)

> Count of in-patient (IP) encounters that are not assigned to a bed under the fake beds root location

## Purpose

Returns the total number of active in-patient (`encounter_class = 'imp'`) encounters at SSMM that are **not** linked to any bed under the fake beds root location (`root_location_id = 300`).

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filter by encounter creation date range | `emr_encounter.created_date BETWEEN '2026-04-01' AND '2026-04-30'` |

---

## Query

```sql
SELECT 
    COUNT(DISTINCT e.id) AS encounter_count
FROM emr_encounter e
JOIN emr_facilitylocationencounter fle ON fle.encounter_id = e.id
JOIN emr_facilitylocation fl ON fle.location_id = fl.id
WHERE e.encounter_class = 'imp'
  AND e.deleted = FALSE
  AND fl.deleted = FALSE
  AND fl.status = 'active'
  AND fl.form = 'bd'
  AND fle.deleted = FALSE
  AND fl.root_location_id != 300
  --[[AND {{date}}]]
```


## Notes

- Restricted to in-patient encounters (`encounter_class = 'imp'`) that are non-deleted.
- Hardcoded to `fl.root_location_id = 300` — the fake beds root location. Update if the fake-beds root ID changes.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards

*Last updated: 2026-05-04*

````
