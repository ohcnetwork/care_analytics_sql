
# Nursing Procedures Count by Facility 

> Count of specific nursing procedures performed per facility for patients in a given organization

## Purpose

Counts how many times each of a defined set of nursing procedures was recorded in community-nurse questionnaire responses (`questionnaire_id = 3`), grouped by facility.


## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `organization_id` | TEXT | Organization external ID to scope facilities (matched against `emr_organization.external_id`, joined via `facility_facility.geo_organization_cache`) | `'org-uuid-1234'` |
| `visit_date` | DATE / range | Metabase date filter (typically bound to `emr_questionnaireresponse.created_date`) | `'2026-07-01'` |

---

## Query

```sql
WITH org_id AS (
    SELECT emr_organization.id
    FROM emr_organization
    WHERE emr_organization.deleted = FALSE
     -- AND emr_organization.external_id::text = {{organization_id}}
),
filtered_encounters AS (
    SELECT
        emr_encounter.id,
        emr_encounter.patient_id,
        facility_facility.name AS facility_name
    FROM emr_encounter
    INNER JOIN facility_facility
        ON facility_facility.id = emr_encounter.facility_id
       AND facility_facility.deleted = FALSE
    INNER JOIN org_id
        ON facility_facility.geo_organization_cache && ARRAY[org_id.id]::integer[]
    WHERE emr_encounter.status NOT IN ('entered_in_error', 'cancelled')
),
procedure_rows AS (
    SELECT
        filtered_encounters.facility_name,
        proc_val ->> 'value' AS nursing_procedure
    FROM emr_questionnaireresponse
    INNER JOIN filtered_encounters
        ON filtered_encounters.id = emr_questionnaireresponse.encounter_id
    INNER JOIN emr_patient
        ON emr_patient.id = emr_questionnaireresponse.patient_id
       AND emr_patient.deleted = FALSE
       AND emr_patient.deceased_datetime IS NULL
    CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS proc_resp
    CROSS JOIN LATERAL jsonb_array_elements(proc_resp -> 'values') AS proc_val
    WHERE emr_questionnaireresponse.deleted = FALSE
      AND emr_questionnaireresponse.questionnaire_id = 3
      AND emr_questionnaireresponse.encounter_id IS NOT NULL
      AND proc_resp ->> 'question_id' = 'd2e39c72-8a19-463b-b92f-3f7b7a9d76ad'
      AND proc_val ->> 'value' IN (
          'BED_BATH',
          'ASCITIC_TAPPING',
          'RYLE''S_TUBE_INSERTION',
          'CATHETER_CHANGE',
          'CATHETER_INSERTION',
          'PER_RECTAL_EXAMINATION',
          'INFUSIONS',
          'INJECTIONS'
      )
      --[[AND {{visit_date}}]]
)
SELECT
    procedure_rows.facility_name AS "Facility",
    procedure_rows.nursing_procedure AS "Nursing Procedure",
    COUNT(*) AS "Count"
FROM procedure_rows
GROUP BY
    procedure_rows.facility_name,
    procedure_rows.nursing_procedure
ORDER BY
    procedure_rows.facility_name,
    "Count" DESC;
```


## Notes

- **Hardcoded IDs:**
  - `questionnaire_id = 3` — the community-nurse questionnaire.
  - `d2e39c72-8a19-463b-b92f-3f7b7a9d76ad` — the nursing-procedures question UUID.
  Update both if the questionnaire or question changes.
- **`organization_id` is required** (no `[[...]]` wrapper) — the query will not run without a value.
- **Metabase filter:**
  - `[[AND {{visit_date}}]]` is a field filter — bind it to `emr_questionnaireresponse.created_date`.
- Results are ordered by facility name, then by procedure count descending within each facility.

*Last updated: 2026-08-03*
