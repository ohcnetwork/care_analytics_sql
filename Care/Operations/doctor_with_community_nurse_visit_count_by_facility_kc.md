
# Doctor with Community Nurse Visit Count by Facility 

> Count of completed doctor visits accompanied by a community nurse, grouped by facility for patients belonging to a given organization

## Purpose

Counts completed responses to the doctor visit questionnaire (`questionnaire_id = 68`)  where the visit type is `'Doctor with Community Nurse'`, per facility, scoped to living patients within a specified organization.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `organization_id` | TEXT | Organization external ID to scope patients (matched against `emr_organization.external_id`) | `'org-uuid-1234'` |
| `date` | DATE / range | Metabase date filter (typically bound to `emr_questionnaireresponse.created_date`) | `'2026-07-01'` |

---

## Query

```sql
WITH org_id AS (
    SELECT emr_organization.id
    FROM emr_organization
    WHERE emr_organization.deleted = FALSE
      --AND emr_organization.external_id::text = {{organization_id}}
),
filtered_patients AS (
    SELECT emr_patient.id
    FROM emr_patient
    INNER JOIN org_id ON TRUE
    WHERE emr_patient.deceased_datetime IS NULL
      AND emr_patient.organization_cache && ARRAY[org_id.id]::integer[]
),
doctor_visits AS (
    SELECT DISTINCT
        emr_questionnaireresponse.id AS response_id,
        emr_questionnaireresponse.encounter_id,
        DATE(emr_questionnaireresponse.created_date) AS visit_date
    FROM emr_questionnaireresponse
    INNER JOIN filtered_patients
        ON filtered_patients.id = emr_questionnaireresponse.patient_id
    CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS response_element
    WHERE emr_questionnaireresponse.questionnaire_id = 68
      AND emr_questionnaireresponse.status = 'completed'
      AND emr_questionnaireresponse.encounter_id IS NOT NULL
      AND response_element ->> 'question_id' = '8d5c73c2-b5ba-4b6f-9d0f-295a4c105fec'
      AND response_element -> 'values' -> 0 ->> 'value' = 'Doctor with Community Nurse'
      --[[AND {{date}}]]
)
SELECT
    facility_facility.name AS facility_name,
    COUNT(DISTINCT doctor_visits.response_id) AS visit_count
FROM doctor_visits
INNER JOIN emr_encounter
    ON emr_encounter.id = doctor_visits.encounter_id
INNER JOIN facility_facility
    ON facility_facility.id = emr_encounter.facility_id
   AND facility_facility.deleted = FALSE
GROUP BY facility_facility.name
ORDER BY visit_count DESC, facility_facility.name;
```

## Notes

- **Hardcoded IDs:**
  - `questionnaire_id = 68` — the doctor visit questionnaire at Karunashraya.
- **`organization_id` is required** (no `[[...]]` wrapper) — the query will not run without a value.
- Results are ordered by visit count descending, then alphabetically by facility name for ties.

*Last updated: 2026-07-15*
