
# Open Encounters Report - SSMM

> List of open encounters (planned, in progress, or discharged) with the creating staff, patient details and SSMM ID

## Purpose

Operational report that surfaces every "still open" encounter at SSMM so that clinical and admin teams can follow up: close encounters that should be closed, chase pending discharges, etc. Inpatient (`imp`) encounters are only included when the patient is actually occupying a real bed.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created` | DATE / range | Metabase date filter on `e.created_date` | `'2026-05-01'` |
| `encounter_class` | TEXT | Filter by encounter class (e.g. `imp`, `amb`, `emer`) | `'imp'` |
| `status` | TEXT | Filter by encounter status | `'in_progress'` |

---

## Query

```sql
SELECT
    TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS staff_name,
    p.name AS patient_name,
    p.phone_number,
    p.gender,
    p.year_of_birth,
    pi.value AS ssmm_id,
    e.encounter_class,
    e.status AS encounter_status,
    e.created_date
FROM emr_encounter e
JOIN emr_patient p ON e.patient_id = p.id
JOIN users_user u ON e.created_by_id = u.id
LEFT JOIN emr_patientidentifier pi ON e.patient_id = pi.patient_id AND pi.config_id = 21
WHERE e.status IN ('planned', 'in_progress', 'discharged')
  AND (
    e.encounter_class != 'imp'
    OR EXISTS (
      SELECT 1
      FROM emr_facilitylocationencounter fle
      JOIN emr_facilitylocation fl ON fle.location_id = fl.id
      WHERE fle.encounter_id = e.id
        AND fle.deleted = FALSE
        AND fl.deleted = FALSE
        AND fl.status = 'active'
        AND fl.form = 'bd'
        AND fl.root_location_id != 300
    )
  )
  --[[AND {{created}}]]
  --[[AND e.encounter_class = {{encounter_class}}]]
  --[[AND e.status = {{status}}]]
ORDER BY e.created_date DESC;
```


## Notes

- **Open encounter definition** — `e.status IN ('planned', 'in_progress', 'discharged')`. `discharged` is included because such encounters are not yet financially / clinically closed 
- **Inpatient filter** — for `encounter_class = 'imp'`, the encounter is only included if the patient currently has at least one **real, active bed** assigned via `emr_facilitylocationencounter`. The bed must be:
  - `form = 'bd'` (a bed-type location),
  - `status = 'active'` and not deleted,
  - and not under the fake-beds root (`root_location_id != 300`).
  - Non-inpatient encounters (`amb`, `emer`, etc.) bypass this check.
- **Hardcoded values:**
  - `pi.config_id = 21` — the identifier config representing the SSMM ID. Update if the config ID changes.
  - `fl.root_location_id != 300` — excludes the fake beds root. Update if the fake-beds root ID changes.
- **Metabase filters** — allow dashboard users to narrow down by date, class, or status.
- Results are ordered by most recently created encounter first.

*Last updated: 2026-05-22*

