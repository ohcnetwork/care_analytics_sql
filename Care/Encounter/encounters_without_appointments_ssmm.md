
# Encounters Without Appointments 

> Identifies patient's op encounter that was created without a linked appointment

## Purpose

Identifies op (`encounter_class = 'amb'`) encounters at SSMM that were created **without** a linked appointment (`appointment_id IS NULL`) .

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE / range | Metabase date filter (required, bound to `e.created_date`) | `'2026-07-01'` |

---

## Query

```sql
SELECT 
    p.name AS patient_name,
    pi.value AS ssmm_id,
    e.created_date,
    TRIM(COALESCE(u.first_name, '') || ' ' || u.last_name, '') AS created_by
FROM emr_encounter e
JOIN emr_patient p
    ON e.patient_id = p.id
LEFT JOIN emr_patientidentifier pi
    ON p.id = pi.patient_id
   AND pi.config_id = 21
LEFT JOIN users_user u
    ON e.created_by_id = u.id
WHERE e.encounter_class = 'amb'
  AND e.appointment_id IS NULL
  --[[AND {{date}}]]
ORDER BY e.patient_id, e.created_date;
```

## Notes

- Results are effectively ordered by patient (via `DISTINCT ON`), then earliest encounter date within each patient.

*Last updated: 2026-07-24*
