# Pain Score

> Returns the count of pain score forms filled, with optional filters for visit date, patient, and staff.

## Purpose

To track the number of pain score forms filled for patients, supporting pain management and quality of care.

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
	COUNT(*) AS pain_score_forms_filled
FROM emr_questionnaireresponse qr
JOIN emr_patient p ON qr.patient_id = p.id
LEFT JOIN users_user u ON qr.created_by_id = u.id
WHERE qr.questionnaire_id = 27
	
		--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
		[[AND {{visit_date}} ]]
		[[AND p.name = {{patient_name}} ]]
		[[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
	*/
;
```



## Drill-Down Query

> Returns detailed pain score form information for each patient, including demographics, staff, and pain score value.

### Purpose

To provide a detailed list of pain score form responses for each patient, supporting clinical review and patient-level analysis.

### Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `visit_date`   | DATE   | Filter by visit date (optional)             | '2025-12-01'   |
| `patient_name` | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`   | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

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
	(
		SELECT val ->> 'value'
		FROM jsonb_array_elements(qr.responses) resp
			JOIN LATERAL jsonb_array_elements(resp -> 'values') val ON TRUE
		WHERE resp ->> 'question_id' = 'pain_score_question_id'
		LIMIT 1
	) AS pain_score
FROM emr_questionnaireresponse qr
JOIN emr_patient p ON qr.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
LEFT JOIN users_user u ON qr.created_by_id = u.id
WHERE qr.questionnaire_id = 27
	
		--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
		[[AND {{visit_date}} ]]
		[[AND p.name = {{patient_name}} ]]
		[[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
	*/
ORDER BY qr.created_date DESC, patient_name;
```

## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The queries use `questionnaire_id = 27` to identify the pain score form.
- The `pain_score_question_id` should be replaced with the actual question_id for the pain score in your form.
- The `config_id = 5` condition is used to select the correct Medical Record number (MRnumber) for each patient.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-15*
