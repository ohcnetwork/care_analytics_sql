
# Count of Patients with High RBS

> Count of patients whose latest recorded RBS value is greater than 150

## Purpose

Counts patients whose most recent recorded RBS value from the specified questionnaire is above `150`. 

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
					(answer_element->>'value')::numeric AS systolic_bp
		FROM emr_questionnaireresponse
		CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS response_element
		CROSS JOIN LATERAL jsonb_array_elements(response_element->'values') AS answer_element
		WHERE emr_questionnaireresponse.status = 'completed'
			AND emr_questionnaireresponse.questionnaire_id IN (115)
			AND response_element->>'question_id' = 'b000f459-1efb-4e1b-9579-2e568f9aa510'
			--[[AND {{date_filter}}]]
		ORDER BY emr_questionnaireresponse.patient_id, emr_questionnaireresponse.created_date DESC
)
SELECT COUNT(*) AS patients_with_rbs
FROM latest_sbp
WHERE latest_sbp.systolic_bp > 150;
```

## Notes

- **Hardcoded IDs:**
	- `questionnaire_id = 115` identifies the questionnaire.
	- `question_id = 'b000f459-1efb-4e1b-9579-2e568f9aa510'` identifies the RBS field.
	Update these if the form configuration changes.
- **Metabase filter:** `[[AND {{date_filter}}]]` is a field filter — bind it to `emr_questionnaireresponse.created_date`.

*Last updated: 2026-08-11*
