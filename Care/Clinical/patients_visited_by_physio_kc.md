
# Patients Visited by Physiotherapists

> Count of unique living patients who received a physiotherapist visit

## Purpose

Returns the total count of patients who got a physiotherapist visit. Filterable by facility, date, and the staff member who recorded the response.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facility_id` | TEXT | Filter by facility external ID (exact match on `facility_facility.external_id`) | `'facility-uuid-1234'` |
| `date` | DATE / range | Metabase date filter (typically bound to `emr_questionnaireresponse.created_date`) | `'2026-07-01'` |
| `staff_name` | TEXT | Filter by the full name of the staff who recorded the response (prefix + first + last) | `'Dr. Jane Smith'` |

---

## Query

```sql
WITH nurse_responses AS (
    SELECT
        emr_questionnaireresponse.patient_id
    FROM emr_questionnaireresponse
    JOIN emr_encounter
        ON emr_encounter.id = emr_questionnaireresponse.encounter_id
    JOIN facility_facility
        ON facility_facility.id = emr_encounter.facility_id
    JOIN emr_patient
        ON emr_patient.id = emr_questionnaireresponse.patient_id
    JOIN users_user
        ON users_user.id = emr_questionnaireresponse.created_by_id
    WHERE emr_questionnaireresponse.questionnaire_id = 265
      AND emr_questionnaireresponse.status = 'completed'
      AND emr_questionnaireresponse.encounter_id IS NOT NULL
      AND emr_patient.deceased_datetime IS NULL
      --[[AND facility_facility.external_id::text = {{facility_id}}]]
      --[[AND {{date}}]]
      --[[AND TRIM(COALESCE(users_user.prefix || ' ', '') || users_user.first_name || ' ' || users_user.last_name, '') = {{staff_name}}]]
)
SELECT
    COUNT(patient_id) AS homecare_patient_count
FROM nurse_responses;
```

## Notes

- **Questionnaire filter:** `questionnaire_id = 265` is the physio home-care questionnaire. Update if the questionnaire id changes.
- **Completed responses only:** `status = 'completed'` 

*Last updated: 2026-07-15*
