# Patients Requiring Continuous Care

> Track the count of patients requiring continuous caregiver support

## Purpose

Monitor and identify patients who require continuous caregiver support based on the latest care assessment. Helps track care needs and resource planning for patients requiring ongoing support.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facility_id` | TEXT | Filter by facility external ID (optional) | `6909ac5e-37b5-4ff7-8311-65610685ed44` |
| `date` | DATE | Filter by assessment date range (optional) | `2025-12-01 TO 2025-12-31` |
| `staff_name` | TEXT | Filter by staff member who recorded assessment (optional) | `Jane Smith` |

---

## Query

```sql
WITH
  all_care_entries AS (
    SELECT
      emr_questionnaireresponse.patient_id,
      emr_questionnaireresponse.questionnaire_id,
      val ->> 'value' AS care,
      emr_questionnaireresponse.created_date,
      facility_facility.name AS facility_name
    FROM
      emr_questionnaireresponse
      CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS elem
      CROSS JOIN LATERAL jsonb_array_elements(elem -> 'values') AS val
      JOIN emr_questionnaire ON emr_questionnaireresponse.questionnaire_id = emr_questionnaire.id
      JOIN users_user ON emr_questionnaireresponse.created_by_id = users_user.id
      LEFT JOIN emr_encounter ON emr_questionnaireresponse.encounter_id = emr_encounter.id
      LEFT JOIN facility_facility ON emr_encounter.facility_id = facility_facility.id
    WHERE
      emr_questionnaireresponse.questionnaire_id IN (3)
      AND elem ->> 'question_id' IN ('8cbd24e7-3d47-43fb-8f69-3632cba1d149')
      --   [[AND facility_facility.external_id::text = {{facility_id}}]]
      --   [[AND {{date}}]]
      --   [[AND (users_user.first_name || ' ' || users_user.last_name) = {{staff_name}}]]
  ),
  latest_per_patient AS (
    SELECT DISTINCT
      ON (patient_id) patient_id,
      care,
      facility_name,
      questionnaire_id,
      created_date
    FROM
      all_care_entries
    ORDER BY
      patient_id,
      created_date DESC
  )
SELECT
  COUNT(*) AS current_continuous_caregiver_support
FROM
  latest_per_patient
WHERE
  REPLACE(UPPER(care), ' ', '_') = 'CONTINUOUS_CAREGIVER_SUPPORT';
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query uses two CTEs: `all_care_entries` extracts all care values from questionnaire responses, and `latest_per_patient` selects the most recent care assessment per patient.
- Uses `DISTINCT ON (patient_id)` to select the latest care assessment per patient, ordered by `created_date DESC`.
- Questionnaire_id = 3 identifies care requirement assessment forms and is instance-specific.
- Question_id `8cbd24e7-3d47-43fb-8f69-3632cba1d149` identifies care support requirement responses and is instance-specific.
- Care values are extracted from nested JSONB arrays using two CROSS JOIN LATERAL operations on `responses` and `values`.
- The final WHERE clause filters for continuous caregiver support using `REPLACE(UPPER(care), ' ', '_') = 'CONTINUOUS_CAREGIVER_SUPPORT'` to normalize spacing and case.
- Facility filter uses `external_id::text` to match facility external identifiers.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
