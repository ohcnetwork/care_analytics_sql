
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
    WHERE emr_organization.deleted = false
      --AND emr_organization.external_id::text = {{organization_id}}
),
filtered_encounters AS (
    SELECT emr_encounter.id,
           emr_encounter.patient_id,
           emr_encounter.facility_id
    FROM emr_encounter
    INNER JOIN facility_facility
        ON facility_facility.id = emr_encounter.facility_id
       AND facility_facility.deleted = false
    INNER JOIN org_id
        ON facility_facility.geo_organization_cache && ARRAY[org_id.id]::integer[]
     WHERE emr_encounter.status NOT IN ('entered_in_error', 'cancelled')
),
community_nurse_visits AS (
    SELECT DISTINCT
        emr_questionnaireresponse.id AS questionnaireresponse_id,
        filtered_encounters.encounter_id,
        filtered_encounters.facility_id,
        DATE(emr_questionnaireresponse.created_date) AS visit_date
    FROM (
        SELECT filtered_encounters.id AS encounter_id,
               filtered_encounters.patient_id,
               filtered_encounters.facility_id
        FROM filtered_encounters
    ) AS filtered_encounters
    INNER JOIN emr_questionnaireresponse
        ON emr_questionnaireresponse.encounter_id = filtered_encounters.encounter_id
    INNER JOIN emr_patient
        ON emr_patient.id = emr_questionnaireresponse.patient_id
       AND emr_patient.deleted = false
       AND emr_patient.deceased_datetime IS NULL
    CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS response_element
    CROSS JOIN LATERAL jsonb_array_elements(response_element -> 'values') AS answer_element
    WHERE emr_questionnaireresponse.deleted = false
      AND emr_questionnaireresponse.questionnaire_id IN (3, 67)
      AND emr_questionnaireresponse.status = 'completed'
      AND emr_questionnaireresponse.encounter_id IS NOT NULL
      AND response_element ->> 'question_id' IN (
          'd602b9b2-d4cd-43d7-99d3-3d0169095eba',
          'edf6799d-88c4-4f9d-8ced-552dde6ad6af'
      )
      AND answer_element ->> 'value' = 'Community Nurse'
      --[[AND {{date}}]]
)
SELECT
    facility_facility.name AS facility_name,
    COUNT(*) AS community_nurse_visit_count
FROM community_nurse_visits
INNER JOIN facility_facility
    ON facility_facility.id = community_nurse_visits.facility_id
   AND facility_facility.deleted = false
GROUP BY
    community_nurse_visits.facility_id,
    facility_facility.name
ORDER BY
    
    facility_facility.name;
```

## Notes

- **Hardcoded IDs:**
  - `questionnaire_id IN (3, 67)` — community nurse questionnaires
  Update if questionnaires or questions change.
- **`organization_id` is required** (no `[[...]]` wrapper) — the query will not run without a value.
- Results are ordered by visit count descending, then alphabetically by facility name for ties.

*Last updated: 2026-07-15*
