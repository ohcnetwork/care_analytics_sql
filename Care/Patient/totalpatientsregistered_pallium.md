# Total Patients Registered

> Returns the total number of patients registered.

## Purpose

To provide a count of all patients registered, optionally filtered by patient name or staff who registered them. Useful for tracking patient registration trends and staff performance.

## Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `patient_name` | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`   | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

## Query

```sql
SELECT
  COUNT(emr_patient.id) AS total_patient_count
FROM
  emr_patient
LEFT JOIN users_user s ON emr_patient.created_by_id = s.ID

---The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:

/*
WHERE 1=1
  [[AND emr_patient.name = {{patient_name}} ]]
  [[AND CONCAT(s.first_name, ' ', s.last_name) = {{staff_name}} ]]
*/
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- Ensure `users_user` table and `created_by_id` are correctly mapped.
- No hardcoded values; all filters are optional.



---


## Drill-Down Query

> Returns detailed patient information for the total patients registered, including link center, demographics, and staff details.

### Purpose

To provide a detailed breakdown of each registered patient, including their link center, demographics, MR number, and the staff who registered them. This supports deeper analysis and patient-level insights.

### Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `link_center`  | TEXT   | Filter by link center (optional)            | 'CENTER A'     |
| `patient_name` | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`   | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |
| `visit_date`   | DATE   | Filter by visit/registration date (optional)| '2025-12-01'   |

---

```sql
WITH latest_link_center AS (
  SELECT DISTINCT ON (patient_id)
    emr_questionnaireresponse.patient_id,
    emr_questionnaireresponse.responses
  FROM emr_questionnaireresponse
  WHERE emr_questionnaireresponse.questionnaire_id IN (17)
  ORDER BY patient_id, created_date DESC
),
link_center_status AS (
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
    ) AS link_center
  FROM latest_link_center lr,
    jsonb_array_elements(lr.responses) AS resp,
    jsonb_array_elements(resp -> 'values') AS val
  WHERE resp ->> 'question_id' IN (
    '697792a5-6240-4486-ad47-82298af35ab7'
  )
)
SELECT
  lcs.link_center,
  p.name AS patient_name,
  p.gender,
  p.phone_number,
  EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
  p.address,
  pi.value AS MRnumber,
  TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS staff_name,
  p.created_date AS patient_created_date
FROM emr_patient p
LEFT JOIN link_center_status lcs ON p.id = lcs.patient_id
LEFT JOIN emr_patientidentifier pi ON p.id = pi.patient_id AND pi.config_id = 5
LEFT JOIN users_user u ON p.created_by_id = u.id
WHERE
  p.deleted = FALSE
  
    ---The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    
    /*
    [[AND lcs.link_center ILIKE '%' || {{link_center}}|| '%' ]]
    [[AND p.name = {{patient_name}} ]]
    [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
    [[AND  {{visit_date}} ]]
  */
ORDER BY p.created_date DESC, patient_name;
```

## Drill-Down Notes

- Uses CTEs to extract the latest link center from questionnaire responses.
- The CTE uses `questionnaire_id = 17` to extract the link center from the relevant form responses.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The `pi.config_id = 5` condition ensures only relevant MR numbers are included.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.


*Last updated: 2025-12-15*