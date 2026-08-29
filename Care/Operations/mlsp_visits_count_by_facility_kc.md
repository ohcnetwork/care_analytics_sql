
# MLSP Visits Count by Facility

> Count of completed MLSP questionnaire visits grouped by facility for patients belonging to a given organization

## Purpose

Counts completed responses to the MLSP questionnaire (`questionnaire_id = 69`) per facility, scoped to living patients within a specified organization.

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
    SELECT
        emr_encounter.id,
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
visits AS (
    SELECT
        emr_questionnaireresponse.id,
        emr_questionnaireresponse.encounter_id
    FROM emr_questionnaireresponse
    INNER JOIN filtered_encounters
        ON filtered_encounters.id = emr_questionnaireresponse.encounter_id
    WHERE emr_questionnaireresponse.deleted = false
      AND emr_questionnaireresponse.questionnaire_id = 69
      AND emr_questionnaireresponse.status = 'completed'
      AND emr_questionnaireresponse.encounter_id IS NOT NULL
      --[[AND {{date}}]]
)
SELECT
    facility_facility.name AS facility_name,
    COUNT(*) AS visit_count
FROM visits
INNER JOIN emr_encounter
    ON emr_encounter.id = visits.encounter_id
   AND emr_encounter.deleted = false
INNER JOIN facility_facility
    ON facility_facility.id = emr_encounter.facility_id
   AND facility_facility.deleted = false
GROUP BY facility_facility.name
ORDER BY  facility_facility.name;
```

## Notes

- **Hardcoded IDs:**
  - `questionnaire_id = 69` — the MLSP questionnaire. Update if the questionnaire id changes.
- **`organization_id` is required** (no `[[...]]` wrapper) — the query will not run without a value.
- Results are ordered by visit count descending, then alphabetically by facility name for ties.

*Last updated: 2026-07-15*
