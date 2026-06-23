# Nursing Services 

> Returns the count of patients by nursing services provided, with optional filters for visit date, patient, staff, and link center.

## Purpose

To analyze the distribution of nursing services provided to patients, supporting clinical reporting and service utilization analysis.

## Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `visit_date`   | DATE   | Filter by visit date (optional)             | '2025-12-01'   |
| `patient_name` | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`   | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

## Query

```sql
WITH responses AS (
  SELECT
    emr_questionnaireresponse.patient_id,
    emr_questionnaireresponse.created_date,
    emr_questionnaireresponse.created_by_id,
    emr_questionnaireresponse.questionnaire_id,
    resp ->> 'question_id' AS question_id,
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
    LEFT JOIN emr_encounter e ON emr_questionnaireresponse.encounter_id = e.id,
    jsonb_array_elements(emr_questionnaireresponse.responses) AS resp,
    jsonb_array_elements(resp -> 'values') AS val
  WHERE
    emr_questionnaireresponse.questionnaire_id IN (17, 15)
    AND resp ->> 'question_id' IN (
      'df782138-3239-4ce9-91fc-17f7f00fb456',
      'b5b910c6-46b2-4c7c-94ef-1f83b68b0af0'
    )
    
     -- The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
      [[AND {{visit_date}}]]
    */
)
SELECT
  r.response_value AS PROCEDURE,
  COUNT(DISTINCT (r.patient_id, r.created_date)) AS patient_count
FROM
  responses r
JOIN emr_patient p ON r.patient_id = p.id
LEFT JOIN users_user u ON r.created_by_id = u.id
WHERE 1=1
  
    --The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
  /*
    [[AND p.name = {{patient_name}} ]]
    [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
  */
GROUP BY
  r.response_value
ORDER BY
  patient_count DESC;
```


## Drill-Down Query

> Returns detailed patient information for each nursing service provided, including staff, encounter, and link center.

### Purpose

To provide a detailed list of patients for each nursing service, supporting patient-level review and service tracking.

### Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `visit_date`   | DATE   | Filter by visit date (optional)             | '2025-12-01'   |
| `procedure`    | TEXT   | Filter by nursing service (optional)        | 'WOUND CARE'   |
| `patient_name` | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `link_center`  | TEXT   | Filter by link center (optional)            | 'CENTER A'     |
| `staff_name`   | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

```sql
-- CTE to get latest link_center per patient
WITH latest_link_center AS (
  SELECT DISTINCT ON (qr.patient_id)
    qr.patient_id,
    UPPER(
      TRIM(
        REPLACE(
          COALESCE(val ->> 'value', val -> 'coding' ->> 'display'),
          '_',
          ' '
        )
      )
    ) AS link_center,
    qr.created_date
  FROM
    emr_questionnaireresponse qr,
    jsonb_array_elements(qr.responses) AS resp,
    jsonb_array_elements(resp -> 'values') AS val
  WHERE
    qr.questionnaire_id IN (17)
    AND resp ->> 'question_id' = '697792a5-6240-4486-ad47-82298af35ab7'
    
     -- The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
      [[AND {{visit_date}}]]
    */
  ORDER BY
    qr.patient_id, qr.created_date DESC
)

-- Main drilldown query
SELECT
  r.response_value AS procedure,
  p.name AS patient_name,
  p.gender,
  p.phone_number,
  EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
  p.address,
  pi.value AS MRnumber,
  TRIM(s.first_name || ' ' || COALESCE(s.last_name, '')) AS staff_name,
  r.created_date,
  r.questionnaire_id,
  e.encounter_class,
  llc.link_center
FROM (
  SELECT
    qr.patient_id,
    qr.created_date,
    qr.created_by_id,
    qr.questionnaire_id,
    qr.encounter_id,
    resp ->> 'question_id' AS question_id,
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
    emr_questionnaireresponse qr,
    jsonb_array_elements(qr.responses) AS resp,
    jsonb_array_elements(resp -> 'values') AS val
  WHERE
    qr.questionnaire_id IN (17, 15)
    AND resp ->> 'question_id' IN (
      'df782138-3239-4ce9-91fc-17f7f00fb456',
      'b5b910c6-46b2-4c7c-94ef-1f83b68b0af0'
    )
    
     -- The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
     /*
      [[AND {{visit_date}}]]
    */
) r
JOIN emr_patient p ON r.patient_id = p.id
LEFT JOIN emr_encounter e ON r.encounter_id = e.id
LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
LEFT JOIN users_user s ON r.created_by_id = s.id
LEFT JOIN latest_link_center llc ON llc.patient_id = p.id
WHERE
  p.deleted = FALSE
  
    --The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
  /*
    [[AND r.response_value = {{procedure}}  ]]
    [[AND p.name = {{patient_name}}  ]]
    [[AND llc.link_center ILIKE '%' || {{link_center}} || '%']]
    [[AND TRIM(s.first_name || ' ' || COALESCE(s.last_name, '')) = {{staff_name}} ]]
  */
ORDER BY r.created_date DESC, patient_name;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The queries use `questionnaire_id IN (17, 15)` to identify nursing services related forms.
- Specific question_ids are used to extract services provided data.
- The drill-down query includes the latest link center per patient using a CTE.
- The `config_id = 5` condition is used to select the correct Medical Record number (MRnumber) for each patient.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-15*
