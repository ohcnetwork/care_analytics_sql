# Bladder Catheter Method 

> Returns the count of patients by bladder catheter status, with optional filters for visit date, patient, and staff.

## Purpose

To analyze the distribution of bladder catheter methods/status among patients, supporting clinical reporting and device management.

## Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `visit_date`   | DATE   | Filter by visit date (optional)             | '2025-12-01'   |
| `patient_name` | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`   | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

## Query

```sql
WITH latest_responses AS (
	SELECT DISTINCT ON (patient_id)
		emr_questionnaireresponse.patient_id,
		emr_questionnaireresponse.responses,
		emr_questionnaireresponse.created_by_id
	FROM emr_questionnaireresponse
	WHERE emr_questionnaireresponse.questionnaire_id IN (17)
		
			--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
        /*
			[[AND {{visit_date}}]]
		*/
	ORDER BY patient_id, created_date DESC
),
responses AS (
	SELECT
		lr.patient_id,
		lr.created_by_id,
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
		latest_responses lr,
		jsonb_array_elements(lr.responses) AS resp,
		jsonb_array_elements(resp -> 'values') AS val
	WHERE
		resp ->> 'question_id' IN (
			'808f625b-3df1-4b4e-830e-9ee08f6a01b9'
		)
)
SELECT
	r.status AS "Status",
	COUNT(DISTINCT r.patient_id) AS "Patient Count"
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
	r.status
ORDER BY
	"Patient Count" DESC;
```



## Drill-Down Query

> Returns detailed patient information for each bladder catheter status, including demographics, staff, and device details.

### Purpose

To provide a detailed list of patients for each bladder catheter status, supporting patient-level review and device management.

### Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `visit_date`   | DATE   | Filter by visit date (optional)             | '2025-12-01'   |
| `catheter_type`| TEXT   | Filter by catheter type (optional)          | 'FOLEY'        |
| `status`       | TEXT   | Filter by bladder catheter status (optional)| 'CBD'      |
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
		emr_questionnaireresponse.questionnaire_id = 17
		
			--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
        /*
			[[AND {{visit_date}}]]
		*/
	ORDER BY patient_id, created_date DESC
),
drill_data AS (
	SELECT
		p.name AS patient_name,
		p.gender,
		p.phone_number,
		EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
		pi.value AS MRnumber,
		lr.created_date,
		TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS staff_name,
		UPPER(
			TRIM(
				REPLACE(
					COALESCE(
						MAX(CASE WHEN resp->>'question_id' = '808f625b-3df1-4b4e-830e-9ee08f6a01b9' THEN val->>'value' END),
						MAX(CASE WHEN resp->>'question_id' = '808f625b-3df1-4b4e-830e-9ee08f6a01b9' THEN val->'coding'->>'display' END)
					),
					'_', ' '
				)
			)
		) AS status,
		MAX(CASE 
			WHEN resp->>'question_id' = 'c64c2638-6ce0-4814-97b2-5fda4832c30a' THEN val->>'value'
			WHEN resp->>'question_id' = 'd9708732-385a-4559-9169-2989837aa0fb' THEN val->>'value'
			END
		) AS catheter_type,
		MAX(CASE WHEN resp->>'question_id' = 'ec38712c-21d2-4fae-b9b6-d29b788c2c06' THEN val->>'value' END) AS issues,
		MAX(CASE WHEN resp->>'question_id' = 'dc94d0fd-8986-4fa9-b76e-79223cb73f3a' THEN val->>'value' END) AS size,
		MAX(CASE WHEN resp->>'question_id' = '30f32642-f04a-48b5-8cf3-36eeb0f5c5d5' THEN val->>'value' END) AS sterile_water_uses,
		MAX(CASE WHEN resp->>'question_id' = '1086dea0-5aa4-4e4f-9209-533cc20f4d7a' THEN val->>'value' END) AS change_on,
		MAX(CASE WHEN resp->>'question_id' = '7b2b8458-3a12-4f85-b142-2efc7ef1a6c3' THEN val->>'value' END) AS next_catheter_change_date
	FROM latest_responses lr
	JOIN emr_patient p ON p.id = lr.patient_id
	LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
	LEFT JOIN users_user u ON lr.created_by_id = u.id
	LEFT JOIN LATERAL jsonb_array_elements(lr.responses) AS resp ON TRUE
	LEFT JOIN LATERAL jsonb_array_elements(COALESCE(resp->'values', '[]'::jsonb)) AS val ON TRUE
	WHERE resp->>'question_id' IN (
			'808f625b-3df1-4b4e-830e-9ee08f6a01b9',
			'c64c2638-6ce0-4814-97b2-5fda4832c30a',
			'd9708732-385a-4559-9169-2989837aa0fb',
			'ec38712c-21d2-4fae-b9b6-d29b788c2c06',
			'dc94d0fd-8986-4fa9-b76e-79223cb73f3a',
			'30f32642-f04a-48b5-8cf3-36eeb0f5c5d5',
			'1086dea0-5aa4-4e4f-9209-533cc20f4d7a',
			'7b2b8458-3a12-4f85-b142-2efc7ef1a6c3'
	)
	AND (
		(val->>'value' IS NOT NULL AND val->>'value' <> '') OR
		(val->'coding'->>'display' IS NOT NULL AND val->'coding'->>'display' <> '')
	)
	GROUP BY p.id, p.name, p.gender, p.phone_number, p.meta, pi.value, lr.created_date, u.first_name, u.last_name
)
SELECT *
FROM drill_data
--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
/*
WHERE 1=1
		[[AND catheter_type ILIKE '%' || {{catheter_type}} || '%']]
		[[AND status ILIKE '%' || {{status}} || '%']]
		[[AND patient_name ={{patient_name}} ]]
		[[AND staff_name {{staff_name}} ]]
*/
ORDER BY created_date DESC, patient_name;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The queries use `questionnaire_id = 17` and specific question_ids to extract bladder catheter status and related details.
- The `config_id = 5` condition is used to select the correct Medical Record number (MRnumber) for each patient.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-15*
