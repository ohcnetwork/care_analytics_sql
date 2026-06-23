# Mobility Split

> Analyze patient distribution across all mobility status categories

## Purpose

Track and analyze the distribution of patients by mobility status based on the latest assessment. Helps monitor mobility patterns and patient care needs across the organization.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facility_id` | TEXT | Filter by facility external ID (optional) | `6909ac5e-37b5-4ff7-8311-65610685ed44` |
| `date` | DATE | Filter by assessment date range (optional) | `2025-12-01 TO 2025-12-31` |
| `staff_name` | TEXT | Filter by staff member who conducted assessment (optional) | `Jane Smith` |

---

## Query

```sql
SELECT
  mobility AS Mobility,
  COUNT(*) AS count
FROM (
    SELECT DISTINCT ON (emr_questionnaireresponse.patient_id)
           (rs -> 'values' -> 0 ->> 'value') AS mobility
    FROM public.emr_questionnaireresponse
    JOIN public.emr_questionnaire
        ON emr_questionnaireresponse.questionnaire_id = emr_questionnaire.id
    LEFT JOIN users_user ON 
        emr_questionnaireresponse.created_by_id = users_user.id
    LEFT JOIN emr_encounter 
        ON emr_questionnaireresponse.encounter_id = emr_encounter.id
    LEFT JOIN facility_facility 
        ON emr_encounter.facility_id = facility_facility.id
    LEFT JOIN public.emr_patient
        ON emr_questionnaireresponse.patient_id = emr_patient.id
    CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS rs
    WHERE (rs ->> 'question_id') IN (
              'a9d443eb-a71c-4288-b285-f4b7310a4f69'
          )
      AND emr_patient.deceased_datetime IS NULL
      --   [[AND facility_facility.external_id::text = {{facility_id}}]]
      --   [[AND {{date}}]]
      --   [[AND (users_user.first_name || ' ' || users_user.last_name) = {{staff_name}}]]
    ORDER BY emr_questionnaireresponse.patient_id, emr_questionnaireresponse.created_date DESC
) AS query
GROUP BY mobility
ORDER BY count DESC;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query uses a subquery with `DISTINCT ON (emr_questionnaireresponse.patient_id)` to select the latest mobility assessment per patient, ordered by `created_date DESC`.
- Filters out deceased patients using `emr_patient.deceased_datetime IS NULL`.
- The question_id `a9d443eb-a71c-4288-b285-f4b7310a4f69` identifies mobility assessment responses and is instance-specific.
- Facility filter uses `external_id::text` to match facility external identifiers.
- Results are grouped by mobility status and ordered by count in descending order (most common status first).
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
