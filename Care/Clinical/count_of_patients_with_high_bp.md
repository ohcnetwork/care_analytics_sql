
# Count of Patients with High BP

> Count of patients whose latest recorded systolic blood pressure is greater than 140

## Purpose

Counts patients whose most recent recorded systolic blood pressure from the specified questionnaire is above `140`.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date_filter` | DATE / range | Metabase date filter (typically bound to `emr_questionnaireresponse.created_date`) | `'2026-08-01'` |

---

## Query

```sql
WITH latest_sbp AS (
		SELECT DISTINCT ON (emr_questionnaireresponse.patient_id)
					 emr_questionnaireresponse.patient_id AS patient_id,
					 NULLIF(regexp_replace(answer_element->>'value', '[^0-9.]', '', 'g'), '')::numeric AS systolic_bp
		FROM emr_questionnaireresponse
		CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS response_element
		CROSS JOIN LATERAL jsonb_array_elements(response_element->'values') AS answer_element
		WHERE emr_questionnaireresponse.deleted = FALSE
			AND emr_questionnaireresponse.questionnaire_id IN (115)
			AND response_element->>'question_id' = '66464c74-fee5-4a08-9283-f811564a06fb'
			--[[AND {{date_filter}}]]
		ORDER BY emr_questionnaireresponse.patient_id, emr_questionnaireresponse.created_date DESC
)
SELECT COUNT(*) AS patients_with_systolic_bp_gt
FROM latest_sbp
WHERE latest_sbp.systolic_bp > 140;
```

## Notes

- **Hardcoded IDs:**
	- `questionnaire_id = 115` identifies the blood pressure questionnaire.
	- `question_id = '66464c74-fee5-4a08-9283-f811564a06fb'` identifies the systolic blood pressure field.
	Update these if the form configuration changes.
- **Metabase filter:** `[[AND {{date_filter}}]]` is a field filter — bind it to `emr_questionnaireresponse.created_date`.

*Last updated: 2026-08-11*
