
# Incomplete OP Encounters - SSMM

> Out-patient (OP) encounters created more than a day ago that are still not completed.

## Purpose

Identifies out-patient (`encounter_class = 'amb'`) encounters at SSMM that were created more than 24 hours ago but have not been completed — i.e., their current `status` is still not one of `completed`, `cancelled`, or `entered_in_error`. 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created_date` | DATE | Filter by encounter creation date range | `e.created_date BETWEEN '2026-04-01' AND '2026-04-30'` |

---

## Query

```sql
SELECT 
    p.name AS patient_name,
    pi.value AS ssmm_id,
    e.created_date AS encounter_created_date,
    e.status AS current_status,
    TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS created_by
FROM emr_encounter e
JOIN emr_patient p ON p.id = e.patient_id
LEFT JOIN emr_patientidentifier pi
    ON p.id = pi.patient_id
   AND pi.config_id = 21
JOIN users_user u ON u.id = e.created_by_id
WHERE e.encounter_class = 'amb'
  AND e.deleted = FALSE
  AND e.status NOT IN ('completed', 'cancelled', 'entered_in_error')
  AND e.created_date < CURRENT_TIMESTAMP - INTERVAL '1 day'
  --[[AND {{created_date}}]]
ORDER BY e.created_date DESC;
```


## Notes

- Restricted to OP encounters (`encounter_class = 'amb'`) that are non-deleted.
- Hardcoded to `pi.config_id = 21` — the SSMM patient identifier configuration. Update if the config changes.
- Sorted by `created_date DESC` so the most recently created stale encounters appear first.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.

*Last updated: 2026-05-04*

````
