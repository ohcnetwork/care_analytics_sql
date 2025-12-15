# ESAS-r Forms Filled (Pallium)

> Returns the count of ESAS-r forms filled, with optional filters for date, patient, and staff.

## Purpose

To track the number of ESAS-r (Edmonton Symptom Assessment System - revised) forms filled for patients, supporting symptom monitoring and quality of care.

## Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `date`        | DATE   | Filter by form date (optional)              | '2025-12-01'   |
| `patient_name`| TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`  | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

## Query

```sql
SELECT
  COUNT(*) AS forms_filled_count
FROM emr_questionnaireresponse qr
JOIN emr_patient p ON qr.patient_id = p.id
JOIN users_user u ON qr.created_by_id = u.id
WHERE qr.questionnaire_id = 26
  
    --The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
    [[AND {{date}} ]]
    [[AND p.name = {{patient_name}} ]]
    [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
  */
;
```



## Drill-Down Query

> Returns detailed ESAS-r form information for each patient, including staff, and all ESAS-r symptom fields.

### Purpose

To provide a detailed list of ESAS-r form responses for each patient, supporting clinical review and patient-level analysis.

### Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `date`        | DATE   | Filter by form date (optional)              | '2025-12-01'   |
| `patient_name`| TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`  | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

```sql
SELECT
  p.name AS patient_name,
  p.gender,
  EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
  pi.value AS MRnumber,
  p.phone_number,
  qr.created_date AS form_created_date,
  TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS staff_name,
  -- Each question as separate column
  (
    SELECT val ->> 'value'
    FROM jsonb_array_elements(qr.responses) resp
      JOIN LATERAL jsonb_array_elements(resp -> 'values') val ON TRUE
    WHERE resp ->> 'question_id' = 'f960e788-a131-4764-a3ea-b25e8586f004'
    LIMIT 1
  ) AS pain,
  (
    SELECT val ->> 'value'
    FROM jsonb_array_elements(qr.responses) resp
      JOIN LATERAL jsonb_array_elements(resp -> 'values') val ON TRUE
    WHERE resp ->> 'question_id' = '9147b7b1-db85-44ad-b071-34ac4aff3019'
    LIMIT 1
  ) AS tiredness,
  (
    SELECT val ->> 'value'
    FROM jsonb_array_elements(qr.responses) resp
      JOIN LATERAL jsonb_array_elements(resp -> 'values') val ON TRUE
    WHERE resp ->> 'question_id' = '8db8d2b6-3660-4b19-9a80-7f7cd8f7de03'
    LIMIT 1
  ) AS drowsiness,
  (
    SELECT val ->> 'value'
    FROM jsonb_array_elements(qr.responses) resp
      JOIN LATERAL jsonb_array_elements(resp -> 'values') val ON TRUE
    WHERE resp ->> 'question_id' = 'c2fb0cbe-6e74-486f-ba02-1f9f81291739'
    LIMIT 1
  ) AS nausea,
  (
    SELECT val ->> 'value'
    FROM jsonb_array_elements(qr.responses) resp
      JOIN LATERAL jsonb_array_elements(resp -> 'values') val ON TRUE
    WHERE resp ->> 'question_id' = '6d1836fb-d163-4524-a3a2-3dc7c99054dc'
    LIMIT 1
  ) AS shortness_of_breath,
  (
    SELECT val ->> 'value'
    FROM jsonb_array_elements(qr.responses) resp
      JOIN LATERAL jsonb_array_elements(resp -> 'values') val ON TRUE
    WHERE resp ->> 'question_id' = '7e95e2c7-8c98-482a-8cd6-448e2fd4fca6'
    LIMIT 1
  ) AS depression,
  (
    SELECT val ->> 'value'
    FROM jsonb_array_elements(qr.responses) resp
      JOIN LATERAL jsonb_array_elements(resp -> 'values') val ON TRUE
    WHERE resp ->> 'question_id' = 'cdaf2000-7fc6-4bee-9a73-c6ed106f3397'
    LIMIT 1
  ) AS anxiety,
  (
    SELECT val ->> 'value'
    FROM jsonb_array_elements(qr.responses) resp
      JOIN LATERAL jsonb_array_elements(resp -> 'values') val ON TRUE
    WHERE resp ->> 'question_id' = '9ecc4269-8d7a-4822-9921-7ef0c1e63515'
    LIMIT 1
  ) AS best_wellbeing,
  (
    SELECT val ->> 'value'
    FROM jsonb_array_elements(qr.responses) resp
      JOIN LATERAL jsonb_array_elements(resp -> 'values') val ON TRUE
    WHERE resp ->> 'question_id' = '668ad395-4a92-47f0-89a8-58cd83a599a7'
    LIMIT 1
  ) AS no_other_problem
FROM emr_questionnaireresponse qr
JOIN emr_patient p ON qr.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
LEFT JOIN users_user u ON qr.created_by_id = u.id
WHERE qr.questionnaire_id = 26
  
    --The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
    [[AND  {{date}} ]]
    [[AND p.name = {{patient_name}} ]]
    [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
  */
ORDER BY qr.created_date DESC, patient_name;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The queries use `questionnaire_id = 26` to identify the ESAS-r form.
- Each question_id (e.g., `f960e788-a131-4764-a3ea-b25e8586f004`) corresponds to a specific ESAS-r symptom and is displayed as a separate column in the drill-down output.
- The `config_id = 5` condition is used to select the correct Medical Record number (MRnumber) for each patient.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-15*
