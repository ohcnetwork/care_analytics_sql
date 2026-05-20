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
WITH first_discharged AS (
    SELECT DISTINCT ON (e.id)
        e.id AS encounter_id,
        e.patient_id,  
        e.status AS current_status,
        (discharged_status->>'moved_at')::timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata' AS discharged_datetime
    FROM emr_encounter e
    CROSS JOIN LATERAL jsonb_array_elements(e.status_history->'history') AS discharged_status
    WHERE e.encounter_class = 'imp'
      AND e.deleted = FALSE
      AND discharged_status->>'status' = 'discharged'
      AND e.status != 'completed'
    ORDER BY e.id, (discharged_status->>'moved_at')::timestamp DESC
)

SELECT 
    p.name AS patient_name,
    pi.value AS ssmm_id,
    fd.discharged_datetime,
    fd.current_status,
    lb.bed_name AS latest_bed,
    lb.bed_assigned_date
FROM first_discharged fd
JOIN emr_patient p ON fd.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON p.id = pi.patient_id AND pi.config_id = 21
JOIN LATERAL (
    SELECT 
        fl.name AS bed_name,
        fle.created_date AS bed_assigned_date
    FROM emr_facilitylocationencounter fle
    JOIN emr_facilitylocation fl ON fle.location_id = fl.id
    WHERE fle.encounter_id = fd.encounter_id
      AND fl.form = 'bd'
      AND fl.root_location_id != 300
    ORDER BY fle.created_date DESC
    LIMIT 1
) lb ON TRUE
WHERE fd.discharged_datetime < CURRENT_TIMESTAMP - INTERVAL '1 day'
ORDER BY p.id, fd.discharged_datetime DESC, p.name
```


## Notes

- **Hardcoded values:**
  - `pi.config_id = 21` — SSMM patient identifier configuration.
  - `fl.root_location_id != 300` — excludes fake beds.
  - `fl.form = 'bd'` — only bed-type facility locations.
- This query has no Metabase parameters; the date threshold is fixed at "more than 1 day ago".

*Last updated: 2026-05-04*

````
