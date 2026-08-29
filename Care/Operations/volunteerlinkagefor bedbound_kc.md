# Volunteer Linkage for Bedbound

> Track the count of bedbound patients linked to volunteer support

## Purpose

Monitor and analyze the number of bedbound patients who have been linked to volunteer support. Helps track volunteer resource allocation and ensures bedbound patients have appropriate community support.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facility_id` | TEXT | Filter by facility external ID (optional) | `6909ac5e-37b5-4ff7-8311-65610685ed44` |
| `date` | DATE | Filter by assessment date range (optional) | `2025-12-01 TO 2025-12-31` |
| `staff_name` | TEXT | Filter by staff member who recorded assessment (optional) | `Jane Smith` |

---

## Query

```sql
WITH
  all_mobility_entries AS (
    SELECT
      emr_questionnaireresponse.patient_id,
      emr_questionnaireresponse.questionnaire_id,
      emr_questionnaireresponse.created_date,
      val ->> 'value' AS mobility_value,
      facility_facility.name AS facility_name
    FROM
      emr_questionnaireresponse
      JOIN users_user ON emr_questionnaireresponse.created_by_id = users_user.id
      LEFT JOIN emr_encounter ON emr_questionnaireresponse.encounter_id = emr_encounter.id
      LEFT JOIN facility_facility ON emr_encounter.facility_id = facility_facility.id
      JOIN emr_questionnaire ON emr_questionnaireresponse.questionnaire_id = emr_questionnaire.id
      CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS elem
      CROSS JOIN LATERAL jsonb_array_elements(elem -> 'values') AS val
    WHERE
      emr_questionnaireresponse.questionnaire_id IN (3)
      AND elem ->> 'question_id' IN ('a9d443eb-a71c-4288-b285-f4b7310a4f69')
      --   [[AND facility_facility.external_id::text = {{facility_id}}]]
      --   [[AND {{date}}]]
      --   [[AND (users_user.first_name || ' ' || users_user.last_name) = {{staff_name}}]]
  ),
  latest_per_patient AS (
    SELECT DISTINCT
      ON (patient_id) patient_id,
      questionnaire_id,
      mobility_value,
      facility_name,
      created_date
    FROM
      all_mobility_entries
    ORDER BY
      patient_id,
      created_date DESC
  ),
  all_volunteer_links AS (
    SELECT DISTINCT
      emr_patientuser.patient_id
    FROM
      emr_patientuser
    WHERE
      emr_patientuser.role_id = 7
      AND emr_patientuser.deleted = FALSE
  ),
  bedbound_with_linkage AS (
    SELECT
      latest_per_patient.patient_id,
      CASE
        WHEN all_volunteer_links.patient_id IS NOT NULL THEN 'Yes'
        ELSE 'No'
      END AS volunteer_linkage
    FROM
      latest_per_patient
      LEFT JOIN all_volunteer_links ON latest_per_patient.patient_id = all_volunteer_links.patient_id
    WHERE
      latest_per_patient.mobility_value ILIKE '%Bedbound%'
  ),
  counts AS (
    SELECT
      SUM(
        CASE
          WHEN volunteer_linkage = 'Yes' THEN 1
          ELSE 0
        END
      ) AS yes_count
    FROM
      bedbound_with_linkage
  )
SELECT
  COALESCE(yes_count, 0) AS yes_count
FROM
  counts;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query uses five CTEs organized for clarity:
  - `all_mobility_entries`: Extracts all mobility assessments from questionnaire responses
  - `latest_per_patient`: Selects the latest mobility assessment per patient using DISTINCT ON
  - `all_volunteer_links`: Identifies patients linked to volunteers (role_id = 7)
  - `bedbound_with_linkage`: Joins bedbound patients with volunteer linkage status
  - `counts`: Aggregates the final count
- Questionnaire_id = 3 identifies mobility assessment forms and is instance-specific.
- Question_id `a9d443eb-a71c-4288-b285-f4b7310a4f69` identifies mobility status responses and is instance-specific.
- Mobility values are extracted from nested JSONB arrays using two CROSS JOIN LATERAL operations.
- Role_id = 7 identifies volunteer relationships in the emr_patientuser table and is instance-specific.
- Only non-deleted volunteer links are included using `emr_patientuser.deleted = FALSE`.
- Facility filter uses `external_id::text` to match facility external identifiers.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
