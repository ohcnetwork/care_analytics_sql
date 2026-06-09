
# Laboratory Service Requests by Patient Count - SSMM

> Number of completed laboratory service requests per patient per day.

## Purpose

Identifies patients with the highest volume of laboratory service requests at SSMM. 

## Parameters

*No parameters — the query returns all completed laboratory service requests.*

---

## Query

```sql

SELECT 
    DATE(sr.created_date) AS created_date,
    p.name AS patient_name,
    pi.value AS ssmm_id,
    COUNT(*) AS request_count
FROM emr_servicerequest sr
JOIN emr_patient p
  ON sr.patient_id = p.id
LEFT JOIN emr_patientidentifier pi
  ON p.id = pi.patient_id
 AND pi.config_id = 21
WHERE sr.status = 'completed'
  AND sr.category = 'laboratory'
GROUP BY
    sr.patient_id,
    DATE(sr.created_date),
    p.name,
    pi.value
ORDER BY request_count DESC;
```


## Notes

- Only service requests with `status = 'completed'` and `category = 'laboratory'` are counted.
- **Hardcoded values:**
  - `pi.config_id = 21` — the identifier config representing the SSMM ID. Update if the config ID changes.
  - `sr.category = 'laboratory'` — restricts to lab requests; change to widen/narrow the scope (e.g. `'imaging'`).
- Results are ordered by highest `request_count` first, so top lab consumers surface at the top.
- No date filter is applied — the result spans all history. Add a `[[AND {{created_date}}]]` clause if a Metabase date filter is needed.

*Last updated: 2026-05-22*


