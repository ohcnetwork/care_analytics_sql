
# IP Encounter Count - SSMM (Excluding Fake Beds)

> Count of in-patient (IP) encounters that are not assigned to a bed under the fake beds root location

## Purpose

Returns the total number of active in-patient (`encounter_class = 'imp'`) encounters at SSMM that are **not** linked to any bed under the fake beds root location (`root_location_id = 300`).

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created_date` | DATE | Filter by encounter creation date range | `emr_encounter.created_date BETWEEN '2026-04-01' AND '2026-04-30'` |

---

## Query

```sql
SELECT 
    COUNT(*) AS encounter_count
FROM emr_encounter
WHERE emr_encounter.encounter_class = 'imp'
  AND emr_encounter.deleted = FALSE
  AND NOT EXISTS (
      SELECT 1
      FROM emr_facilitylocationencounter fle
      JOIN emr_facilitylocation fl ON fle.location_id = fl.id
      WHERE fle.encounter_id = emr_encounter.id
        AND fl.root_location_id = 300
  )
  --[[AND {{created_date}}]];
```


## Notes

- Restricted to in-patient encounters (`encounter_class = 'imp'`) that are non-deleted.
- Hardcoded to `fl.root_location_id = 300` — the fake beds root location. Update if the fake-beds root ID changes.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards

*Last updated: 2026-05-04*

````
