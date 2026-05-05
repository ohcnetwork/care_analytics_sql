````markdown
# IP Encounter List - SSMM (Excluding Fake Beds)

> Detailed list of in-patient (IP) encounters that are not assigned to any bed under the fake beds root location, with patient, SSMM ID, and current bed details

## Purpose

Returns a per-encounter list of active in-patient (`encounter_class = 'imp'`) admissions at SSMM that are **not** linked to any bed under the fake beds root location (`root_location_id = 300`), along with the patient details (including SSMM ID), the staff who created the encounter, and the latest **real** bed assignment (and who assigned it).


## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created_date` | DATE | Filter by encounter creation date range | `e.created_date BETWEEN '2026-04-01' AND '2026-04-30'` |

---

## Query

```sql
SELECT DISTINCT ON (e.id)
    p.name AS patient_name,
    pi.value AS ssmm_id,
    TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS staff_name,
    e.created_date,
    fl.name AS bed_name,
    fle.created_date AS bed_assigned_date,
    TRIM(u2.first_name || ' ' || COALESCE(u2.last_name, '')) AS bed_assigned_by
FROM emr_encounter e
JOIN emr_patient p ON e.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON p.id = pi.patient_id AND pi.config_id = 21
JOIN users_user u ON e.created_by_id = u.id
JOIN emr_facilitylocationencounter fle ON fle.encounter_id = e.id
JOIN emr_facilitylocation fl ON fle.location_id = fl.id
LEFT JOIN users_user u2 ON fle.created_by_id = u2.id
WHERE e.encounter_class = 'imp'
  AND e.deleted = FALSE
  AND fl.deleted = FALSE
  AND fl.status = 'active'
  AND fl.form = 'bd'
  AND fle.deleted = FALSE
  AND fl.root_location_id != 300
  --[[AND {{start_date}}]]
ORDER BY e.id, fle.created_date DESC;
```


## Notes

- Restricted to in-patient encounters (`encounter_class = 'imp'`) that are non-deleted.
- Hardcoded values:
  - `fl.root_location_id = 300` — the fake beds root location. Update if the fake-beds root ID changes.
  - `fl.form = 'bd'` — only bed-type facility locations.
  - `pi.config_id = 21` — SSMM patient identifier configuration. Update if the config changes.
- `SELECT DISTINCT ON (e.id) ... ORDER BY e.id, fle.created_date DESC` keeps only the **latest** real bed assignment per encounter when an encounter has multiple `fle` rows.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
*Last updated: 2026-05-04*

````
