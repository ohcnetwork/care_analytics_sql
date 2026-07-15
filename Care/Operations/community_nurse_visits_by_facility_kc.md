
# Community Nurse Visits by Facility

> Count of community nurse visits grouped by facility for patients belonging to a given organization

## Purpose

Counts the number of completed community-nurse visits per facility, scoped to living patients within a specified organization.

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
     -- AND emr_organization.external_id::text = {{organization_id}}
),
filtered_patients AS (
    SELECT emr_patient.id
    FROM emr_patient
    INNER JOIN org_id ON TRUE
    WHERE emr_patient.deceased_datetime IS NULL
      AND emr_patient.organization_cache && ARRAY[org_id.id]::integer[]
),
community_nurse_visits AS (
    SELECT DISTINCT
        emr_questionnaireresponse.id AS questionnaireresponse_id,
        emr_questionnaireresponse.encounter_id,
        DATE(emr_questionnaireresponse.created_date) AS visit_date
    FROM emr_questionnaireresponse
    INNER JOIN filtered_patients
        ON filtered_patients.id = emr_questionnaireresponse.patient_id
    CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS response_element
    CROSS JOIN LATERAL jsonb_array_elements(response_element -> 'values') AS answer_element
    WHERE emr_questionnaireresponse.questionnaire_id IN (3, 67)
      AND emr_questionnaireresponse.status = 'completed'
      AND emr_questionnaireresponse.encounter_id IS NOT NULL
      AND response_element ->> 'question_id' IN (
            'd602b9b2-d4cd-43d7-99d3-3d0169095eba',
            'edf6799d-88c4-4f9d-8ced-552dde6ad6af'
      )
      AND answer_element ->> 'value' = 'Community Nurse'
      --[[AND {{date}}]]
),
visit_with_facility AS (
    SELECT
        community_nurse_visits.visit_date,
        facility_facility.id AS facility_id,
        facility_facility.name AS facility_name
    FROM community_nurse_visits
    INNER JOIN emr_encounter
        ON emr_encounter.id = community_nurse_visits.encounter_id
    INNER JOIN facility_facility
        ON facility_facility.id = emr_encounter.facility_id
       AND facility_facility.deleted = FALSE
)
SELECT
    visit_with_facility.facility_name,
    COUNT(*) AS community_nurse_visit_count
FROM visit_with_facility
GROUP BY
    visit_with_facility.facility_id,
    visit_with_facility.facility_name
ORDER BY
    community_nurse_visit_count DESC,
    visit_with_facility.facility_name;
```

## Notes

- **Hardcoded IDs:**
  - `questionnaire_id IN (3, 67)` — community nurse questionnaires
  Update if questionnaires or questions change.
- **`organization_id` is required** (no `[[...]]` wrapper) — the query will not run without a value.
- Results are ordered by visit count descending, then alphabetically by facility name for ties.

*Last updated: 2026-07-15*
