
# IP Patients Bed Stay Details - SSMM

> Patient-level list of in-patient (IP) encounters with their current/last bed, floor, discharge time, billable bed days and exact stay duration

## Purpose

Line list of in-patient (`encounter_class = 'imp'`) encounters at SSMM showing where each patient is (or was last) bedded and how long they stayed. 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `encounter_date` | DATE | Admission date (encounter `created_date` in IST) | `'2026-11-01'` |
| `practitioner` | TEXT | Full name of the first care-team member (`prefix first last`, trimmed) | `'Dr Asha Menon'` |
| `ssmm_id` | TEXT | Patient's SSMM ID (patient identifier `config_id = 21`) | `'SSMM12345'` |
| `discharge_date` | DATE | Discharge date (encounter `period.end` in IST) | `'2026-11-05'` |

---

## Query

```sql
WITH encounters AS (
    SELECT
        e.external_id AS encounter_external_id,
        e.id AS encounter_id,
        e.created_date,
        e.status,
        p.external_id AS patient_external_id,
        p.name AS patient_name,
        pi.value AS ssmm_id,
        TRIM(CONCAT_WS(' ', doc.prefix, doc.first_name, doc.last_name)) AS practitioner_name
    FROM emr_encounter e
    JOIN emr_patient p ON e.patient_id = p.id
    LEFT JOIN emr_patientidentifier pi ON p.id = pi.patient_id AND pi.config_id = 21
    LEFT JOIN users_user doc ON doc.id = (
        CASE WHEN jsonb_typeof(e.care_team) = 'array' THEN e.care_team -> 0 ->> 'user_id' END
    )::int
    WHERE e.encounter_class = 'imp'
    -- [[AND (e.created_date AT TIME ZONE 'Asia/Kolkata')::date = {{encounter_date}}]]
    -- [[AND TRIM(CONCAT_WS(' ', doc.prefix, doc.first_name, doc.last_name)) = {{practitioner}} ]]
      AND e.deleted = FALSE
      AND e.status != 'entered_in_error'
    --   [[AND pi.value = {{ssmm_id}}]]
),

first_discharged AS (
    SELECT
        e.id AS encounter_id,
        ((e.period->>'end')::timestamptz AT TIME ZONE 'Asia/Kolkata') AS discharged_datetime
    FROM emr_encounter e
    WHERE e.encounter_class = 'imp'
      AND e.deleted = FALSE
      AND e.period->>'end' IS NOT NULL
),

all_beds AS (
    SELECT DISTINCT ON (fle.encounter_id)
        fle.encounter_id,
        fl.name AS bed_name,
        COALESCE(grandparent_loc.name, parent_loc.name) AS floor,
        fle.start_datetime AS start_date
    FROM emr_facilitylocationencounter fle
    JOIN emr_facilitylocation fl ON fle.location_id = fl.id
    LEFT JOIN emr_facilitylocation parent_loc ON fl.parent_id = parent_loc.id
    LEFT JOIN emr_facilitylocation grandparent_loc ON parent_loc.parent_id = grandparent_loc.id
    WHERE fl.form = 'bd'
      AND fl.root_location_id != 300
      AND fle.deleted = FALSE
    ORDER BY fle.encounter_id, fle.start_datetime DESC, fle.created_date DESC
)

SELECT
    e.encounter_external_id,
    e.patient_name,
    e.patient_external_id,
    e.ssmm_id,
    e.practitioner_name,
    e.created_date,
    fd.discharged_datetime,
    e.status,
    ba.floor,
    ba.bed_name,
    GREATEST(
        COALESCE(fd.discharged_datetime::date, (NOW() AT TIME ZONE 'Asia/Kolkata')::date)
            - (e.created_date AT TIME ZONE 'Asia/Kolkata')::date,
        1
    ) AS qty,
    (m.mins / 1440) || ' days ' || ((m.mins % 1440) / 60) || ' hrs ' || (m.mins % 60) || ' min' AS stay_duration
FROM encounters e
JOIN all_beds ba ON e.encounter_id = ba.encounter_id
LEFT JOIN first_discharged fd ON e.encounter_id = fd.encounter_id
CROSS JOIN LATERAL (
    SELECT GREATEST(FLOOR(EXTRACT(EPOCH FROM (
        COALESCE(fd.discharged_datetime, NOW() AT TIME ZONE 'Asia/Kolkata')
            - (e.created_date AT TIME ZONE 'Asia/Kolkata')
    )) / 60), 0)::int AS mins
) m
WHERE TRUE
--   [[AND fd.discharged_datetime::date = {{discharge_date}}]]
ORDER BY e.patient_name, ba.start_date, e.created_date;
```


## Notes

- Only encounters with at least one real bed are returned (inner join to `all_beds`). Beds under the fake beds root location (`root_location_id = 300`) are excluded.
- Admission time is `emr_encounter.created_date`. Discharge time is `period.end`.
- All date logic is in IST (`Asia/Kolkata`). `qty` counts calendar-day boundaries, so a same-day admission/discharge (or an overnight stay under 24 hours) is billed as 1 day.
- For patients still admitted, `qty` and `stay_duration` are calculated up to the current time, so they change on every run.
- Practitioner is the **first** entry in `emr_encounter.care_team`.
- Hardcoded IDs: `pi.config_id = 21` (SSMM ID identifier) and `root_location_id = 300` (fake beds). Update them if these change.
- **Metabase filters:** all four are simple variables (Date / Text), not field filters. Using `discharge_date` drops encounters that haven't been discharged.

*Last updated: 2026-11-23*
