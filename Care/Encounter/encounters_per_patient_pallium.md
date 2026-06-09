
# Encounters Per Patient - Pallium

> Total number of encounters per patient with MRN (patient identifier)

## Purpose

Shows the total encounter count per patient at Pallium along with their MRN.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created_date` | DATE / range | Metabase date filter (bound to `e.created_date`) | `'2026-05-25'` |
| `mrn` | TEXT | Filter by patient MRN (exact match on `emr_patientidentifier.value`) | `'PAL-1023'` |

---

## Query

```sql
SELECT
    p.name AS patient_name,
    pi.value AS mrn,
    COUNT(e.id) AS total_encounters
FROM emr_encounter e
JOIN emr_patient p
  ON e.patient_id = p.id
LEFT JOIN emr_patientidentifier pi
  ON p.id = pi.patient_id
 AND pi.config_id = 4
WHERE e.status NOT IN ('cancelled','entered_in_error')
  --[[AND {{created_date}}]]
  --[[AND pi.value = {{mrn}}]]
GROUP BY p.id, p.name, pi.value
ORDER BY total_encounters DESC, p.name;
```

## Notes

- **Metabase filters:**
  - `[[AND {{created_date}}]]` is a field filter — bind it to `e.created_date` in the Metabase variable settings.
  - `[[AND pi.value = {{mrn}}]]` is an exact-match text filter on the patient's MRN.
- `pi.config_id = 4` selects the MRN identifier configuration for Pallium — update if the MRN config id differs in another environment.
- Encounters with status `cancelled` or `entered_in_error` are excluded.

*Last updated: 2026-06-09*
