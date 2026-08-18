
# Appointments Per Patient - Pallium

> Total number of appointments per patient with MRN (patient identifier)

## Purpose

Shows the total appointment count per patient at Pallium along with their MRN. 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE / range | Metabase date filter (typically bound to `tb.booked_on` or `ts.start_datetime`) | `'2026-05-25'` |
| `mrn` | TEXT | Filter by patient MRN (exact match on `emr_patientidentifier.value`) | `'PAL-1023'` |

---

## Query

```sql
SELECT
    p.name AS patient_name,
    pi.value AS mrn,
    COUNT(tb.id) AS total_appointments
FROM emr_tokenbooking tb
JOIN emr_tokenslot ts
  ON tb.token_slot_id = ts.id
JOIN emr_patient p
  ON tb.patient_id = p.id
LEFT JOIN emr_patientidentifier pi
  ON p.id = pi.patient_id
 AND pi.config_id = 4
WHERE tb.status NOT IN ('cancelled','entered_in_error')
  AND ts.deleted = FALSE
  --[[AND {{date}}]]
  --[[AND pi.value = {{mrn}}]]
GROUP BY p.id, p.name, pi.value
ORDER BY total_appointments DESC, p.name;
```

## Notes

- **Metabase filters:**
  - `[[AND {{date}}]]` is a field filter — bind it to the appropriate booking/slot date column in the Metabase variable settings.
- `pi.config_id = 4` selects the MRN identifier configuration for Pallium — update if the MRN config id differs in another environment.
- Appointments with status `cancelled` or `entered_in_error` are excluded.
- Soft-deleted token slots (`ts.deleted = TRUE`) are excluded.

*Last updated: 2026-06-09*
