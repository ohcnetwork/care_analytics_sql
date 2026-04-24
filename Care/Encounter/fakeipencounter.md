
# Fake IP Encounters with Bed Assignment

> List of in-patient (IP) encounters that currently hold a bed under the "fake" beds root location (`root_location_id = 300`)

## Purpose

Returns all active in-patient (`encounter_class = 'imp'`) encounters that are currently occupying a bed (`fle.end_datetime IS NULL`) under the **fake beds** root location (`root_location_id = 300`).

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created_date` | DATE | Filter by encounter creation date range | `e.created_date BETWEEN '2026-04-01' AND '2026-04-22'` |

---

## Query

```sql
SELECT DISTINCT ON (e.id)
    p.name AS patient_name,
    pi.value AS ssmm_id,
    e.created_date,
    fl.name AS bed_name,
    fle.created_date AS bed_assigned_date,
    TRIM(u2.first_name || ' ' || COALESCE(u2.last_name, '')) AS bed_assigned_by
FROM emr_encounter e
JOIN emr_patient p ON e.patient_id = p.id
LEFT JOIN emr_patientidentifier pi
    ON p.id = pi.patient_id
   AND pi.config_id = 21
JOIN users_user u ON e.created_by_id = u.id
JOIN emr_facilitylocationencounter fle ON fle.encounter_id = e.id
JOIN emr_facilitylocation fl
    ON fle.location_id = fl.id
   AND fl.form = 'bd'
   AND fl.root_location_id = 300
WHERE e.encounter_class = 'imp'
  AND e.deleted = FALSE
  AND fle.end_datetime IS NULL
  --[[AND {{created_date}}]]
ORDER BY e.id, fle.created_date DESC;
```


## Notes

- Restricted to in-patient encounters (`encounter_class = 'imp'`) that are non-deleted.
- Hardcoded to:
  - `fl.form = 'bd'` — only bed-type facility locations.
  - `fl.root_location_id = 300` — the **fake beds root location**; every bed under this root is treated as a fake/placeholder bed. Update if the root ID changes.
  - `pi.config_id = 21` — SSMM patient identifier configuration (update if the config changes).
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.

*Last updated: 2026-04-24*

````
