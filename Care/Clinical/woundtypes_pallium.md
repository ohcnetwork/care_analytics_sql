# Wound Types 

> Returns the count of patients by wound type (procedure), with optional filters for visit date, patient, and staff.

## Purpose

To analyze the distribution of wound types among patients, supporting clinical reporting and wound care management.

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
		emr_questionnaireresponse.questionnaire_id IN (17)
		AND resp ->> 'question_id' IN (
			'b50632b5-c6ab-4822-87a7-7f2c495ee985'
		)
		
			--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
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

> Returns detailed patient information for each wound type, staff and MR number.

### Purpose

To provide a detailed list of patients for each wound type, supporting patient-level review and wound care management.

### Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `visit_date`   | DATE   | Filter by visit date (optional)             | '2025-12-01'   |
| `wound_type`   | TEXT   | Filter by wound type (optional)             | 'PRESSURE ULCER'|
| `patient_name` | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`   | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

```sql
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
	r.questionnaire_id
FROM (
	SELECT
		qr.patient_id,
		qr.created_date,
		qr.created_by_id,
		qr.questionnaire_id,
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
		qr.questionnaire_id IN (17)
		AND resp ->> 'question_id' IN (
			'b50632b5-c6ab-4822-87a7-7f2c495ee985'
		)
		
			--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
        /*
			[[AND {{visit_date}}]]
		*/
) r
JOIN emr_patient p ON r.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
LEFT JOIN users_user s ON r.created_by_id = s.id
WHERE
	p.deleted = FALSE
	
		--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
		[[AND r.response_value ILIKE '%' || {{wound_type}} || '%' ]]
		[[AND p.name = {{patient_name}}  ]]
		[[AND TRIM(s.first_name || ' ' || COALESCE(s.last_name, '')) = {{staff_name}} ]]
	*/
ORDER BY r.created_date DESC, patient_name;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The queries use `questionnaire_id = 17` and question_id `b50632b5-c6ab-4822-87a7-7f2c495ee985` to identify wound type responses.
- The `config_id = 5` condition is used to select the correct Medical Record number (MRnumber) for each patient.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-15*
