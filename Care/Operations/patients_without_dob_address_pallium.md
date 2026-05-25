
# Patients Without DOB and Address - Pallium

> List of patients who are missing both date of birth and address

## Purpose

Identifies patient records where **both** `date_of_birth` and `address` are missing so the team can follow up and complete the records. 

## Parameters

*No parameters — the query returns all matching patients.*

---

## Query

```sql
SELECT
    p.name AS patient_name,
    p.date_of_birth,
    p.address,
    p.external_id AS external_id,
    pi.value AS ssmm_id
FROM emr_patient p
LEFT JOIN emr_patientidentifier pi ON p.id = pi.patient_id AND pi.config_id = 4
WHERE p.date_of_birth IS NULL 
  AND (p.address IS NULL OR p.address = '')
ORDER BY p.name;
```


## Notes

- **Hardcoded values:**
  - `pi.config_id = 4` — the identifier config representing the Pallium ID. Update if the config ID changes.
- Results are ordered alphabetically by `patient_name`.

*Last updated: 2026-05-25*


`````
