# Patients on Antibiotics 

> Returns the count of antibiotic forms filled for patients, with optional filters for visit date, patient, and staff.

## Purpose

To track the number of patients for whom the antibiotics form was filled and patient care monitoring.

## Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `visit_date`   | DATE   | Filter by visit date (optional)             | '2025-12-01'   |
| `patient_name` | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`   | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

## Query

```sql
SELECT
  COUNT(*) AS form_count
FROM
  emr_questionnaireresponse qr
JOIN emr_patient p ON qr.patient_id = p.id
LEFT JOIN users_user u ON qr.created_by_id = u.id
WHERE
  qr.questionnaire_id = 25
  AND qr.deleted = false
  
    ---The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
    [[AND {{visit_date}}]]
    [[AND p.name = {{patient_name}} ]]
    [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
  */
;
```



## Drill-Down Query

> Returns detailed antibiotic form information for each patient, staff, and all key antibiotic-related fields.

### Purpose

To provide a detailed list of antibiotic form responses for each patient, supporting clinical review and patient-level analysis.

### Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `visit_date`   | DATE   | Filter by visit date (optional)             | '2025-12-01'   |
| `patient_name` | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`   | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

```sql
WITH latest_responses AS (
  SELECT DISTINCT ON (patient_id)
    emr_questionnaireresponse.patient_id,
    emr_questionnaireresponse.responses,
    emr_questionnaireresponse.created_date,
    emr_questionnaireresponse.created_by_id
  FROM
    emr_questionnaireresponse
  WHERE
    emr_questionnaireresponse.questionnaire_id = 25
    
      ---The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
      /*
      [[AND {{visit_date}}]]
    */
  ORDER BY
    patient_id, created_date DESC
)
SELECT
  p.name AS patient_name,
  p.gender,
  p.phone_number,
  EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
  p.address,
  pi.value AS MRnumber,
  TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS staff_name,
  lr.created_date,
  MAX(CASE WHEN resp->>'question_id' = '9b0bd96b-5602-45f3-bdd8-f54cd0551caa' THEN val->>'value' END) AS Indication_details,
  MAX(CASE WHEN resp->>'question_id' = '15ee191c-9160-4d95-9d00-117a6a414468' THEN val->>'value' END) AS suspected_or_confirmed,
  MAX(CASE WHEN resp->>'question_id' = '1bcf2671-cf72-4e4f-82c3-caf789b52b8a' THEN val->>'value' END) AS cultures_ordered,
  MAX(CASE WHEN resp->>'question_id' = 'dcd38ab3-676c-4290-bba4-b12a5f9ed4c2' THEN val->>'value' END) AS infection_details,
  STRING_AGG(CASE WHEN resp->>'question_id' = '8f330a5a-1d5c-4344-8d6a-2463eb8113d7' THEN val->>'value' END, ', ') AS signs_and_symptoms,
  MAX(CASE WHEN resp->>'question_id' = 'aed32016-1fc2-4da6-a7d8-a167a8d1a5d7' THEN val->>'value' END) AS antibiotic_initiation,
  MAX(CASE WHEN resp->>'question_id' = 'b4f030fd-4f6a-4899-90f8-e94f1c12dd89' THEN val->>'value' END) AS continuation_of_antibiotic_prescribed_outside_of_Pallium,
  MAX(CASE WHEN resp->>'question_id' = '9845cea0-459e-4ec3-bca2-6458d5f9df21' THEN val->>'value' END) AS changing_to_new_antibiotic,
  MAX(CASE WHEN resp->>'question_id' = '3fce4a38-62e6-47ab-8740-ad254b24a65e' THEN val->>'value' END) AS choice_of_antibiotic,
  MAX(CASE WHEN resp->>'question_id' = '266978ec-7a36-4aeb-af04-b578afc7c594' THEN val->>'value' END) AS treatment_duration,
  MAX(CASE WHEN resp->>'question_id' = '61967479-574c-4cf3-ab82-5432c8586469' THEN val->>'value' END) AS antibiotics_provided,
  MAX(CASE WHEN resp->>'question_id' = '50c00c3e-d52f-415c-a954-4d3eb9c01d8a' THEN val->>'value' END) AS education_provided
FROM latest_responses lr
JOIN emr_patient p ON p.id = lr.patient_id
LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
LEFT JOIN users_user u ON lr.created_by_id = u.id
LEFT JOIN LATERAL jsonb_array_elements(lr.responses) AS resp ON TRUE
LEFT JOIN LATERAL jsonb_array_elements(resp -> 'values') AS val ON TRUE
WHERE resp ->> 'question_id' in (
  '9b0bd96b-5602-45f3-bdd8-f54cd0551caa', 
  '15ee191c-9160-4d95-9d00-117a6a414468',
  '1bcf2671-cf72-4e4f-82c3-caf789b52b8a', 
  'dcd38ab3-676c-4290-bba4-b12a5f9ed4c2',
  '8f330a5a-1d5c-4344-8d6a-2463eb8113d7',
  'aed32016-1fc2-4da6-a7d8-a167a8d1a5d7',
  'b4f030fd-4f6a-4899-90f8-e94f1c12dd89',
  '9845cea0-459e-4ec3-bca2-6458d5f9df21', 
  '3fce4a38-62e6-47ab-8740-ad254b24a65e',
  '266978ec-7a36-4aeb-af04-b578afc7c594',
  '61967479-574c-4cf3-ab82-5432c8586469', 
  '50c00c3e-d52f-415c-a954-4d3eb9c01d8a'
)
AND val ->> 'value' IS NOT NULL AND val ->> 'value' <> ''

 ---The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
 /*
  [[AND p.name = {{patient_name}} ]]
  [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
*/
GROUP BY
  p.id, p.name, p.gender, p.phone_number, p.address, p.meta, pi.value, lr.created_date, u.first_name, u.last_name
ORDER BY p.name;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The main and drill-down queries use `questionnaire_id = 25` to identify the antibiotics form.
- Each question_id (e.g., `50c00c3e-d52f-415c-a954-4d3eb9c01d8a`) corresponds to a specific question in the antibiotics form and is displayed as a separate column in the drill-down output.
- The drill-down query extracts the latest antibiotic form per patient and all key antibiotic-related fields.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-15*
