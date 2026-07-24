
# Community Nurse Patients Linked to Volunteers 

> Count of community-nurse home-care patients who are also linked to a volunteer, grouped by facility

## Purpose

Identifies patients who received a completed community-nurse home-care visit at facilities within a given geo-organization, and further narrows to only those patients who also have an active volunteer link (`emr_patientuser.role_id = 7`). 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `organization_id` | TEXT | Organization external ID to scope facilities (matched against `emr_organization.external_id`, joined via `facility_facility.geo_organization_cache`) | `'org-uuid-1234'` |
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
filtered_encounters AS (
    SELECT
        emr_encounter.id,
        emr_encounter.patient_id,
        emr_encounter.facility_id
    FROM emr_encounter
    INNER JOIN facility_facility
        ON facility_facility.id = emr_encounter.facility_id
       AND facility_facility.deleted = FALSE
    INNER JOIN org_id
        ON facility_facility.geo_organization_cache && ARRAY[org_id.id]::integer[]
    WHERE emr_encounter.deleted = FALSE
),
nurse_responses AS (
    SELECT DISTINCT
        emr_questionnaireresponse.patient_id,
        emr_questionnaireresponse.encounter_id,
        DATE(emr_questionnaireresponse.created_date) AS visit_date
    FROM emr_questionnaireresponse
    INNER JOIN filtered_encounters
        ON filtered_encounters.id = emr_questionnaireresponse.encounter_id
    INNER JOIN emr_patient
        ON emr_patient.id = emr_questionnaireresponse.patient_id
       AND emr_patient.deceased_datetime IS NULL
    CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS response_element
    WHERE emr_questionnaireresponse.questionnaire_id IN (3,67)
      AND emr_questionnaireresponse.status = 'completed'
      AND emr_questionnaireresponse.encounter_id IS NOT NULL
      AND response_element ->> 'question_id' in ('d602b9b2-d4cd-43d7-99d3-3d0169095eba', 'edf6799d-88c4-4f9d-8ced-552dde6ad6af')
      AND response_element -> 'values' -> 0 ->> 'value' IN ()'Community Nurse')
      --[[AND {{date}}]]
),
homecare_patients_by_facility AS (
    SELECT DISTINCT
        nurse_responses.patient_id,
        facility_facility.name AS facility_name
    FROM nurse_responses
    INNER JOIN emr_encounter
        ON emr_encounter.id = nurse_responses.encounter_id
    INNER JOIN facility_facility
        ON facility_facility.id = emr_encounter.facility_id
       AND facility_facility.deleted = FALSE
),
all_volunteer_links AS (
    SELECT DISTINCT
        emr_patientuser.patient_id
    FROM emr_patientuser
    WHERE emr_patientuser.deleted = FALSE
      AND emr_patientuser.role_id = 7
)
SELECT
    homecare_patients_by_facility.facility_name,
    COUNT(DISTINCT homecare_patients_by_facility.patient_id) AS patients_linked_to_volunteer_engagement
FROM homecare_patients_by_facility
INNER JOIN all_volunteer_links
    ON all_volunteer_links.patient_id = homecare_patients_by_facility.patient_id
GROUP BY homecare_patients_by_facility.facility_name
ORDER BY patients_linked_to_volunteer_engagement DESC, homecare_patients_by_facility.facility_name;
```

## Notes

- **`organization_id` is required** (no `[[...]]` wrapper) — the query will not run without a value.
- **Metabase filter:**
  - `[[AND {{date}}]]` is a field filter — bind it to `emr_questionnaireresponse.created_date`.
- Results are ordered by count descending, then alphabetically by facility name for ties.

*Last updated: 2026-07-24*
