# Total Nurse Visit

> Analyze nurse visit distribution by nurse type

## Purpose

Track and analyze the distribution of nurse visits by nurse type (Community Nurse, Secondary Nurse, MLSP Nurse). Helps monitor nursing service utilization and resource allocation across different nursing categories.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facility_id` | TEXT | Filter by facility external ID (optional) | `6909ac5e-37b5-4ff7-8311-65610685ed44` |
| `date` | DATE | Filter by visit date range (optional) | `2025-12-01 TO 2025-12-31` |
| `staff_name` | TEXT | Filter by staff member who conducted visit (optional) | `Jane Smith` |

---

## Query

```sql
SELECT
  nurse_type,
  COUNT(DISTINCT id) AS patient_count
FROM
  (
    SELECT
      CASE
        WHEN val ->> 'value' = 'Community Nurse' THEN 'Community Nurse'
        WHEN val ->> 'value' = 'Secondary Nurse' THEN 'Secondary Nurse'
        WHEN val ->> 'value' = 'MLSP Nurse' THEN 'MLSP Nurse'
      END AS nurse_type,
      emr_questionnaireresponse.id
    FROM
      emr_questionnaireresponse
      JOIN emr_questionnaire ON emr_questionnaire.id = emr_questionnaireresponse.questionnaire_id
      LEFT JOIN users_user ON users_user.id = emr_questionnaireresponse.created_by_id
      LEFT JOIN emr_encounter ON emr_encounter.id = emr_questionnaireresponse.encounter_id
      LEFT JOIN facility_facility ON facility_facility.id = emr_encounter.facility_id
      CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS elem
      CROSS JOIN LATERAL jsonb_array_elements(elem -> 'values') AS val
    WHERE
      emr_questionnaire.id = 3
      AND emr_questionnaireresponse.deleted = FALSE
      --   [[AND facility_facility.external_id::text = {{facility_id}}]]
      --   [[AND {{date}}]]
      --   [[AND (users_user.first_name || ' ' || users_user.last_name) = {{staff_name}}]]
      AND elem ->> 'question_id' IN ('d602b9b2-d4cd-43d7-99d3-3d0169095eba')
  ) AS nurse_visits
GROUP BY
  nurse_type;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- Questionnaire_id = 3 identifies nursing visit forms and is instance-specific.
- Question_id `d602b9b2-d4cd-43d7-99d3-3d0169095eba` identifies nurse type responses and is instance-specific.
- Only non-deleted questionnaire responses are included using `emr_questionnaireresponse.deleted = FALSE`.
- Three nurse types are recognized: Community Nurse, Secondary Nurse, and MLSP Nurse.
- Facility filter uses `external_id::text` to match facility external identifiers.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
