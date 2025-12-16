# Comfort Devices

> Analyze distribution of comfort and assistive devices provided to patients

## Purpose

Track and analyze the types and distribution of comfort and assistive devices provided to patients based on nursing care assessments. Helps monitor device provision patterns and support resource allocation.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facility_id` | TEXT | Filter by facility external ID (optional) | `6909ac5e-37b5-4ff7-8311-65610685ed44` |
| `visit_date` | DATE | Filter by visit/assessment date range (optional) | `2025-12-01 TO 2025-12-31` |
| `staff_name` | TEXT | Filter by staff member who recorded device (optional) | `Jane Smith` |

---

## Query

```sql
WITH
  nursing_care_questions AS (
    SELECT
      emr_questionnaire.id AS questionnaire_id,
      emr_questionnaire.slug,
      jsonb_array_elements(emr_questionnaire.questions) AS question_block
    FROM
      emr_questionnaire
    WHERE
      emr_questionnaire.id IN (3)
  ),
  nursing_care_qids AS (
    SELECT
      questionnaire_id,
      slug,
      question_block ->> 'id' AS question_id
    FROM
      nursing_care_questions
    WHERE
      question_block ->> 'text' = 'Comfort/Assistive Devices'
  ),
  responses AS (
    SELECT
      emr_questionnaireresponse.patient_id,
      emr_questionnaireresponse.created_date,
      emr_questionnaireresponse.created_by_id,
      UPPER(
        TRIM(
          REPLACE(
            COALESCE(val ->> 'value', val -> 'coding' ->> 'display'),
            '_',
            ' '
          )
        )
      ) AS response_value
    FROM
      emr_questionnaireresponse
      LEFT JOIN users_user ON emr_questionnaireresponse.created_by_id = users_user.id
      LEFT JOIN emr_encounter e ON emr_questionnaireresponse.encounter_id = e.id
      LEFT JOIN facility_facility ON e.facility_id = facility_facility.id,
      jsonb_array_elements(emr_questionnaireresponse.responses) AS resp,
      jsonb_array_elements(resp -> 'values') AS val
    WHERE
      emr_questionnaireresponse.questionnaire_id IN (
        SELECT
          questionnaire_id
        FROM
          nursing_care_qids
      )
      AND resp ->> 'question_id' IN ('e8a7b345-fb6a-4b3e-97b2-4e5cfdb7c4f3')
      --   [[AND facility_facility.external_id::text = {{facility_id}}]]
      --   [[AND {{visit_date}}]]
      --   [[AND (users_user.first_name || ' ' || users_user.last_name) = {{staff_name}}]]
  )
SELECT
  response_value AS PROCEDURE,
  COUNT(DISTINCT (patient_id, created_date)) AS patient_count
FROM
  responses
GROUP BY
  response_value
ORDER BY
  patient_count DESC;
```

## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query uses three CTEs:
  - `nursing_care_questions`: Extracts all question blocks from the nursing care questionnaire
  - `nursing_care_qids`: Filters to find the specific "Comfort/Assistive Devices" question
- Questionnaire_id = 3 identifies nursing care assessment forms and is instance-specific.
- Question_id `e8a7b345-fb6a-4b3e-97b2-4e5cfdb7c4f3` identifies comfort devices responses and is instance-specific.
- Response values are normalized using UPPER, TRIM, and REPLACE to standardize formatting (spaces replaced with underscores)..
- Facility filter uses `external_id::text` to match facility external identifiers.
- Results are ordered by patient count in descending order (most common device first).
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
