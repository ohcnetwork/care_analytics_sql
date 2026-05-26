````markdown
# Discharged but Incomplete IP Encounters - SSMM

> IP encounters that were marked as discharged more than a day ago but are still not marked as completed
## Purpose

Identifies in-patient (`encounter_class = 'imp'`) encounters at SSMM whose status history shows a `discharged` event more than 1 day ago, yet the encounter's current `status` is **not** `completed`.

## Parameters

*This query has no parameters.*

---

## Query

```sql
SELECT 
    p.name AS patient_name,
    pi.value AS ssmm_id,
    fd.discharged_datetime,
    fd.current_status
FROM (
    SELECT DISTINCT ON (e.id)
        e.id AS encounter_id,
        e.patient_id,
        e.status AS current_status,
        (e.period->>'end')::timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata' AS discharged_datetime
    FROM emr_encounter e
    CROSS JOIN LATERAL jsonb_array_elements(e.status_history->'history') h
    WHERE e.encounter_class = 'imp'
      AND e.deleted = FALSE
      AND e.status != 'completed'
      AND h->>'status' = 'discharged'
) fd
JOIN emr_patient p ON p.id = fd.patient_id
LEFT JOIN emr_patientidentifier pi 
    ON pi.patient_id = p.id
   AND pi.config_id = 21
WHERE fd.discharged_datetime < CURRENT_TIMESTAMP - INTERVAL '1 day'
  AND EXISTS (
      SELECT 1
      FROM emr_facilitylocationencounter fle
      JOIN emr_facilitylocation fl ON fl.id = fle.location_id
      WHERE fle.encounter_id = fd.encounter_id
        AND fl.form = 'bd'
        AND fl.root_location_id != 300
  )
ORDER BY p.name;
```


## Notes

- **Hardcoded values:**
  - `pi.config_id = 21` — SSMM patient identifier configuration.
  - `fl.root_location_id != 300` — excludes fake beds.
  - `fl.form = 'bd'` — only bed-type facility locations.
- This query has no Metabase parameters; the date threshold is fixed at "more than 1 day ago".

*Last updated: 2026-05-04*

````
