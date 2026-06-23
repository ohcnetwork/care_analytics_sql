# Patient Status

> Analyze patient status distribution across the organization

## Purpose

Track and analyze patient status distribution based on questionnaire responses. Helps monitor patient status categories and across the care team.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `visit_date` | DATE | Filter by visit date range (optional) | `2025-12-01 TO 2025-12-31` |
| `patient_name` | TEXT | Filter by specific patient (optional) | `John Doe` |
| `staff_name` | TEXT | Filter by staff member (optional) | `Jane Smith` |

---

## Query

```sql
WITH responses AS (
  SELECT
    emr_questionnaireresponse.patient_id,
    emr_questionnaireresponse.created_by_id,
    UPPER(
      TRIM(
        REPLACE(
          COALESCE(val ->> 'value', val -> 'coding' ->> 'display'),
          '_',
          ' '
        )
      )
    ) AS status
  FROM
    emr_questionnaireresponse,
    jsonb_array_elements(emr_questionnaireresponse.responses) AS resp,
    jsonb_array_elements(resp -> 'values') AS val
  WHERE
    emr_questionnaireresponse.questionnaire_id IN (17,15)
    AND resp ->> 'question_id' IN (
      '7f00291f-1514-427c-9d1b-fa5b8810f6d5',
      'a0e4de0f-34ec-4caa-a069-c42bea6a648a'
    )
    --   [[AND {{visit_date}}]]
)
SELECT
  r.status AS "Status",
  COUNT(DISTINCT r.patient_id) AS "Patient Count"
FROM
  responses r
JOIN emr_patient p ON r.patient_id = p.id
LEFT JOIN users_user u ON r.created_by_id = u.id
WHERE p.deleted = false
  --   [[AND p.name = {{patient_name}}]]
  --   [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}}]]
GROUP BY
  r.status
ORDER BY
  "Patient Count" DESC;
```


## Drill-Down Query

> Returns detailed patient information for each status, including demographics, staff attribution, and questionnaire details.

### Purpose

To provide a detailed list of patients for each status type, supporting patient-level review and status tracking.

### Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `visit_date` | DATE | Filter by visit date (optional) | `2025-12-01 TO 2025-12-31` |
| `status` | TEXT | Filter by patient status (optional) | `ACTIVE` |
| `patient_name` | TEXT | Filter by patient name (optional) | `John Doe` |
| `staff_name` | TEXT | Filter by staff full name (optional) | `Jane Smith` |

---

```sql
WITH latest_responses AS (
  SELECT DISTINCT ON (patient_id)
    emr_questionnaireresponse.id,
    emr_questionnaireresponse.patient_id,
    emr_questionnaireresponse.created_by_id,
    emr_questionnaireresponse.created_date,
    emr_questionnaireresponse.questionnaire_id,
    emr_questionnaireresponse.responses
  FROM emr_questionnaireresponse
  WHERE emr_questionnaireresponse.questionnaire_id IN (17,15)
    --   [[AND {{visit_date}}]]
  ORDER BY patient_id, created_date DESC
),
status_table AS (
  SELECT
    lr.patient_id,
    UPPER(
      TRIM(
        REPLACE(
          COALESCE(val ->> 'value', val -> 'coding' ->> 'display'),
          '_',
          ' '
        )
      )
    ) AS status,
    lr.created_by_id,
    lr.created_date,
    lr.questionnaire_id
  FROM latest_responses lr,
    jsonb_array_elements(lr.responses) AS resp,
    jsonb_array_elements(resp -> 'values') AS val
  WHERE resp ->> 'question_id' IN (
    '7f00291f-1514-427c-9d1b-fa5b8810f6d5',
    'a0e4de0f-34ec-4caa-a069-c42bea6a648a'
  )
)
SELECT
  s.status,
  p.name AS patient_name,
  p.gender,
  p.phone_number,
  EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
  p.address,
  pi.value AS MRnumber,
  TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS staff_name,
  s.created_date,
  s.questionnaire_id
FROM status_table s
JOIN emr_patient p ON s.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
LEFT JOIN users_user u ON s.created_by_id = u.id
WHERE
  p.deleted = FALSE
  --   [[AND s.status ILIKE '%' || {{status}} || '%']]
  --   [[AND p.name = {{patient_name}}]]
  --   [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}}]]
ORDER BY s.created_date DESC, patient_name;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query uses `questionnaire_id IN (17, 15)` to identify forms that include status quuestion.
- Status values are extracted using two specific question_ids: `7f00291f-1514-427c-9d1b-fa5b8810f6d5` and `a0e4de0f-34ec-4caa-a069-c42bea6a648a` from each forms respectively.
- The `config_id = 5` condition is used to select the correct Medical Record number (MRnumber) for each patient.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
