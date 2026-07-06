
# Report on Mobility Status of patients

> Patient-level report of the latest mobility status within a given organization, filterable by mobility value and date

## Purpose

For each active (non-deceased) patient belonging to a specified organization, returns the patient's name, address, year of birth, and their **most recent** mobility-status answer (with the response date).

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `organization_id` | TEXT | Organization external ID to scope patients (matched against `emr_organization.external_id`) | `'org-uuid-1234'` |
| `date` | DATE / range | Metabase date filter (typically bound to `emr_questionnaireresponse.created_date`) | `'2026-06-01'` |
| `mobility_status` | TEXT | Filter by the extracted mobility value (exact match) | `'Bedbound'` |

---

## Query

```sql
WITH org_id AS (
    SELECT id
    FROM emr_organization
    WHERE external_id::text = {{organization_id}}
),
filtered_patients AS (
    SELECT
        emr_patient.id,
        emr_patient.name,
        emr_patient.address,
        emr_patient.year_of_birth
    FROM emr_patient, org_id
    WHERE emr_patient.deceased_datetime IS NULL
      AND emr_patient.organization_cache && ARRAY[org_id.id]::INTEGER[]
),
relevant_responses AS (
    SELECT
        emr_questionnaireresponse.patient_id,
        emr_questionnaireresponse.created_date,
        emr_questionnaireresponse.responses
    FROM emr_questionnaireresponse
    WHERE emr_questionnaireresponse.questionnaire_id = 69
      AND emr_questionnaireresponse.status = 'completed'
      AND emr_questionnaireresponse.patient_id IN (SELECT id FROM filtered_patients)
      AND emr_questionnaireresponse.responses @> '[{"question_id": "e4b0d3f4-77fb-4fb6-9213-9c62fa6b5695"}]'
      --[[AND {{date}}]]
),
latest_mobility AS (
    SELECT DISTINCT ON (relevant_responses.patient_id)
        relevant_responses.patient_id,
        rs -> 'values' -> 0 ->> 'value' AS mobility_value,
        relevant_responses.created_date
    FROM relevant_responses
    CROSS JOIN LATERAL jsonb_array_elements(relevant_responses.responses) AS rs
    WHERE rs ->> 'question_id' = 'e4b0d3f4-77fb-4fb6-9213-9c62fa6b5695'
    ORDER BY relevant_responses.patient_id, relevant_responses.created_date DESC
)
SELECT
    filtered_patients.name,
    filtered_patients.address,
    filtered_patients.year_of_birth,
    latest_mobility.mobility_value AS mobility_status,
    latest_mobility.created_date
FROM latest_mobility
JOIN filtered_patients
    ON filtered_patients.id = latest_mobility.patient_id
WHERE 1=1
  --[[AND latest_mobility.mobility_value = {{mobility_status}}]]
ORDER BY filtered_patients.name;
```

## Notes

- **Metabase filters:**
  - `{{organization_id}}` is a required text variable used in the `org_id` CTE.
  - `[[AND {{date}}]]` is a field filter — bind it to `emr_questionnaireresponse.created_date`.
  - `[[AND latest_mobility.mobility_value = {{mobility_status}}]]` is an optional exact-match filter on the mobility answer.
- Results are ordered alphabetically by patient name.

*Last updated: 2026-07-06*
