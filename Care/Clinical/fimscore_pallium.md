# Patients with FIM Scores

> Returns the count of unique patients with FIM scores recorded, with optional filters for visit date, form name, patient, and staff.

## Purpose

To track the number of patients who have Functional Independence Measure (FIM) scores recorded, supporting clinical quality and patient progress monitoring.

## Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `visit_date`   | DATE   | Filter by visit date (optional)             | '2025-12-01'   |
| `form_name`    | TEXT   | Filter by form name (optional)              | 'Physiotherapy followup Form'     |
| `patient_name` | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`   | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

## Query

```sql
SELECT
  COUNT(DISTINCT qr.patient_id) AS patients_with_fim_scores
FROM
  emr_questionnaireresponse qr
  JOIN emr_questionnaire q ON qr.questionnaire_id = q.id
  JOIN emr_patient p ON qr.patient_id = p.id
  LEFT JOIN users_user u ON qr.created_by_id = u.id
  , jsonb_array_elements(qr.responses) AS resp
  , jsonb_array_elements(resp -> 'values') AS val
WHERE
  qr.questionnaire_id IN (19, 20)
  AND resp ->> 'question_id' IN (
    -- Form 19
    '9d2b7f24-d0b8-40af-8477-20e25a1ac4bb',
    'b80b8d6e-ba90-49f3-9bbf-f21f70c049a5',
    '63c57f69-2f83-4871-89de-91e0e689478f',
    -- Form 20
    'a2a6190e-62e8-497f-8e73-677e89c6bb71',
    '82a6c01e-6b41-4dde-982a-0a27747039d5',
    '57a929ca-8ed3-49f3-9bbf-f21f70c049a5'
  )
  AND COALESCE(val ->> 'value', val -> 'coding' ->> 'display') IS NOT NULL
  AND COALESCE(val ->> 'value', val -> 'coding' ->> 'display') <> ''
  
    ---The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
    [[AND {{visit_date}}]]
    [[AND q.title = {{form_name}}]]
    [[AND p.name = {{patient_name}} ]]
    [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
  */
;
```



## Drill-Down Query

> Returns detailed FIM score information for each patient, including form, staff, and score breakdowns.

### Purpose

To provide a detailed list of FIM scores for each patient, supporting clinical review and patient-level analysis.

### Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `visit_date`   | DATE   | Filter by visit date (optional)             | '2025-12-01'   |
| `form_name`    | TEXT   | Filter by form name (optional)              | 'Physiotherapy followup Form'     |
| `patient_name` | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`   | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

```sql
SELECT
  q.title AS form_title,
  p.name AS patient_name,
  p.gender,
  p.phone_number,
  EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
  p.address,
  pi.value AS MRnumber,
  TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS staff_name,
  qr.created_date,
  MAX(CASE WHEN resp ->> 'question_id' IN (
                    '9d2b7f24-d0b8-40af-8477-20e25a1ac4bb',
                    'a2a6190e-62e8-497f-8e73-677e89c6bb71'
                ) THEN (val ->> 'value')::integer END) AS admission_score,
  MAX(CASE WHEN resp ->> 'question_id' IN (
                    'b80b8d6e-ba90-49f3-9bbf-f21f70c049a5',
                    '82a6c01e-6b41-4dde-982a-0a27747039d5'
                ) THEN (val ->> 'value')::integer END) AS discharge_score,
  MAX(CASE WHEN resp ->> 'question_id' IN (
                    '63c57f69-2f83-4871-89de-91e0e689478f',
                    '57a929ca-8ed3-49f3-9bbf-f21f70c049a5'
                ) THEN (val ->> 'value')::integer END) AS follow_up_score,
  COALESCE(
    MAX(CASE WHEN resp ->> 'question_id' IN (
                    '9d2b7f24-d0b8-40af-8477-20e25a1ac4bb',
                    'a2a6190e-62e8-497f-8e73-677e89c6bb71'
                ) THEN (val ->> 'value')::integer END), 0
  ) +
  COALESCE(
    MAX(CASE WHEN resp ->> 'question_id' IN (
                    'b80b8d6e-ba90-49f3-9bbf-f21f70c049a5',
                    '82a6c01e-6b41-4dde-982a-0a27747039d5'
                ) THEN (val ->> 'value')::integer END), 0
  ) +
  COALESCE(
    MAX(CASE WHEN resp ->> 'question_id' IN (
                    '63c57f69-2f83-4871-89de-91e0e689478f',
                    '57a929ca-8ed3-49f3-9bbf-f21f70c049a5'
                ) THEN (val ->> 'value')::integer END), 0
  ) AS total_score
FROM
  emr_questionnaireresponse qr
  JOIN emr_questionnaire q ON qr.questionnaire_id = q.id
  JOIN emr_patient p ON qr.patient_id = p.id
  LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
  LEFT JOIN users_user u ON qr.created_by_id = u.id
  , jsonb_array_elements(qr.responses) AS resp
  , jsonb_array_elements(resp -> 'values') AS val
WHERE
  qr.questionnaire_id IN (19, 20)
  AND resp ->> 'question_id' IN (
    '9d2b7f24-d0b8-40af-8477-20e25a1ac4bb',
    'b80b8d6e-ba90-49f3-9bbf-f21f70c049a5',
    '63c57f69-2f83-4871-89de-91e0e689478f',
    'a2a6190e-62e8-497f-8e73-677e89c6bb71',
    '82a6c01e-6b41-4dde-982a-0a27747039d5',
    '57a929ca-8ed3-49f3-9bbf-f21f70c049a5'
  )
  AND COALESCE(val ->> 'value', val -> 'coding' ->> 'display') IS NOT NULL
  AND COALESCE(val ->> 'value', val -> 'coding' ->> 'display') <> ''
  
    ---The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
    [[AND {{visit_date}}]]
    [[AND q.title = {{form_name}}]]
    [[AND p.name ={{patient_name}} ]]
    [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
  */
GROUP BY
  q.title,
  p.name,
  p.gender,
  p.phone_number,
  p.address,
  p.year_of_birth,
  pi.value,
  u.first_name,
  u.last_name,
  qr.id,
  qr.created_date
ORDER BY
  p.name,
  q.title,
  qr.created_date DESC
```



## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- FIM scores are extracted from questionnaire responses with IDs 19 and 20.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-15*
