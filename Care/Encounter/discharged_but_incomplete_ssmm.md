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
    (e.period->>'end')::timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata' AS discharged_datetime,
    e.status AS current_status
FROM emr_encounter e
JOIN emr_patient p ON p.id = e.patient_id
LEFT JOIN emr_patientidentifier pi 
    ON pi.patient_id = p.id
   AND pi.config_id = 21
WHERE e.encounter_class = 'imp'
  AND e.deleted = FALSE
  AND e.status != 'completed'
  AND e.period->>'end' IS NOT NULL
  AND e.status_history->'history' @> '[{"status": "discharged"}]'::jsonb
  AND (e.period->>'end')::timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
      < CURRENT_TIMESTAMP - INTERVAL '1 day'
  AND EXISTS (
      SELECT 1
      FROM emr_facilitylocationencounter fle
      JOIN emr_facilitylocation fl ON fl.id = fle.location_id
      WHERE fle.encounter_id = e.id
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
