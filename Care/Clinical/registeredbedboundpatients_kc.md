# Bedbound Patient Count

> Track the count of patients with bedbound mobility status

## Purpose

Monitor and analyze the number of patients classified as bedbound based on the latest mobility assessment. Helps identify patients with limited mobility requiring specialized care planning.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facility_id` | TEXT | Filter by facility external ID (optional) | `6909ac5e-37b5-4ff7-8311-65610685ed44` |
| `date` | DATE | Filter by assessment date range (optional) | `2025-12-01 TO 2025-12-31` |
| `staff_name` | TEXT | Filter by staff member who conducted assessment (optional) | `Jane Smith` |

---

## Query

```sql
WITH mobility_raw AS (
  SELECT
    emr_questionnaireresponse.patient_id,
    emr_questionnaireresponse.created_date,
    users_user.first_name || ' ' || COALESCE(users_user.last_name, '') AS staff_full_name,
    (elem -> 'values' -> 0 ->> 'value') AS mobility_value,
    facility_facility.name AS facility_name
  FROM
    emr_questionnaireresponse
    JOIN users_user ON emr_questionnaireresponse.created_by_id = users_user.id
    LEFT JOIN emr_encounter ON emr_questionnaireresponse.encounter_id = emr_encounter.id
    LEFT JOIN facility_facility ON emr_encounter.facility_id = facility_facility.id
    LEFT JOIN emr_patient ON emr_questionnaireresponse.patient_id = emr_patient.id
    CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS elem
  WHERE
    elem ->> 'question_id' IN ('a9d443eb-a71c-4288-b285-f4b7310a4f69')
    AND emr_patient.deceased_datetime IS NULL
    --   [[AND facility_facility.external_id::text = {{facility_id}}]]
    --   [[AND {{date}}]]
    --   [[AND (users_user.first_name || ' ' || users_user.last_name) = {{staff_name}}]]
),
latest_mobility AS (
  SELECT DISTINCT ON (patient_id)
    patient_id,
    staff_full_name,
    facility_name,
    mobility_value,
    created_date
  FROM
    mobility_raw
  ORDER BY
    patient_id,
    created_date DESC
)
SELECT
  COUNT(*) AS bedbound_patient_count
FROM
  latest_mobility
WHERE
  mobility_value ILIKE '%Bedbound%';
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- Uses `DISTINCT ON (patient_id)` to select the latest mobility assessment per patient, ordered by `created_date DESC`.
- Filters out deceased patients using `emr_patient.deceased_datetime IS NULL`.
- The question_id `a9d443eb-a71c-4288-b285-f4b7310a4f69` identifies mobility assessment responses and is instance-specific.
- The final WHERE clause filters for bedbound status using ILIKE pattern matching (`'%Bedbound%'`).
- Facility filter uses `external_id::text` to match facility external identifiers.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
