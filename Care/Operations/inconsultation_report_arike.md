
# In consultation Report - Arike

> List of in consultation appointments at the Arike facility with patient, practitioner and booking-staff details

## Purpose

Operational report for the Arike  team showing every appointment currently in the `in_consultation` state at facility (Arike). For each booking it includes:

- Patient demographics (name, phone, gender, year of birth, ADM ID, deceased flag).
- The practitioner the booking is with.
- The slot's start datetime.



## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE / range | Metabase date filter on the booking (see Notes for which column it binds to) | `'2026-05-25'` |
| `practitioner` | TEXT | Filter by the practitioner's full name (`first_name + last_name`, trimmed) | `'Dr Asha Menon'` |

---

## Query

```sql
SELECT
    p.name AS patient_name,
    p.phone_number,
    p.gender,
    pi.value AS adm,
    p.year_of_birth,
    ts.start_datetime AS init_date,
    TRIM(pr.first_name || ' ' || pr.last_name) AS practitioner,
    CASE WHEN p.deceased_datetime IS NULL THEN 'No' ELSE 'Yes' END AS deceased
FROM emr_tokenbooking tb
JOIN emr_tokenslot ts
  ON tb.token_slot_id = ts.id
JOIN emr_schedulableresource sr
  ON ts.resource_id = sr.id
JOIN users_user pr
  ON sr.user_id = pr.id
JOIN emr_patient p
  ON tb.patient_id = p.id
LEFT JOIN emr_patientidentifier pi
  ON p.id = pi.patient_id
 AND pi.config_id = 2
WHERE sr.facility_id = 2
  AND tb.status = 'in_consultation'
  AND ts.deleted = FALSE
  --[[AND {{created_date}}]]
  --[[AND TRIM(pr.first_name || ' ' || pr.last_name) = {{practitioner}}]]
ORDER BY patient_name;
```


## Notes

- **Hardcoded values:**
  - `sr.facility_id = 2` — the Arike facility ID. Update if pointing to a different facility.
  - `pi.config_id = 2` — the identifier config representing the Arike ADM ID. Update if the config ID changes.
- **Metabase filters** — `[[AND {{date}}]]` is a field filter (bind it to the column you want to filter on in the Metabase UI, typically `ts.start_datetime`), and `[[AND TRIM(pr.first_name || ' ' || pr.last_name) = {{practitioner}}]]` filters by the same expression used to render the `practitioner` column so the value matches what users see.
- Results are ordered alphabetically by `patient_name`.

*Last updated: 2026-05-25*


