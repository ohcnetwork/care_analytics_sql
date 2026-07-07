
# Nursing Care Report with Patient Tags

> Nursing care questionnaire responses with patient tags for zone and place-of-care

## Purpose

Lists nursing-care questionnaire responses (`questionnaire_id = 17`) alongside patient identity (name, phone, gender, ADM identifier) and two patient tags

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `visit_date` | DATE / range | Metabase date filter (typically bound to `emr_questionnaireresponse.created_date`) | `'2026-06-01'` |
| `patient_name` | TEXT | Metabase text filter (typically bound to `emr_patient.name`) | `'John Doe'` |
| `zone_filter` | TEXT | Filter by resolved zone tag display (exact match) | `'Zone A'` |
| `place_of_care` | TEXT | Filter by resolved place-of-care tag display (exact match) | `'Home'` |

---

## Query

```sql
WITH forms AS (
    SELECT
        emr_questionnaire.title AS form_name,
        emr_patient.name AS patient_name,
        emr_patient.phone_number,
        emr_patient.gender,
        emr_patientidentifier.value AS adm,
        COALESCE(
            (SELECT emr_tagconfig.display
             FROM unnest(emr_patient.instance_tags) AS tag_id
             JOIN emr_tagconfig ON emr_tagconfig.id = tag_id
             WHERE emr_tagconfig.parent_id = 55
             LIMIT 1),
            'unassigned'
        ) AS zone,
        COALESCE(
            (SELECT emr_tagconfig.display
             FROM unnest(emr_patient.instance_tags) AS tag_id
             JOIN emr_tagconfig ON emr_tagconfig.id = tag_id
             WHERE emr_tagconfig.parent_id = 71
             LIMIT 1),
            'unassigned'
        ) AS place_of_care,
        emr_questionnaireresponse.created_date AS date
    FROM emr_questionnaireresponse
    JOIN emr_questionnaire
        ON emr_questionnaireresponse.questionnaire_id = emr_questionnaire.id
    JOIN emr_patient
        ON emr_questionnaireresponse.patient_id = emr_patient.id
    LEFT JOIN emr_patientidentifier
        ON emr_patient.id = emr_patientidentifier.patient_id
       AND emr_patientidentifier.config_id = 2
    WHERE emr_questionnaire.id = 17
      --[[AND {{visit_date}}]]
      --[[AND {{patient_name}}]]
)
SELECT *
FROM forms
WHERE 1=1
    --[[AND zone = {{zone_filter}}]]
    --[[AND place_of_care = {{place_of_care}}]]
ORDER BY patient_name;
```

## Notes

- **Hardcoded IDs:**
  - `emr_questionnaire.id = 17` — the nursing-care questionnaire at Arike. Update if the questionnaire id changes.
  - `emr_patientidentifier.config_id = 2` — the ADM identifier configuration at Arike.
  - `parent_id = 55` — parent tag for **zone**.
  - `parent_id = 71` — parent tag for **place of care**.
  Update any of these if the underlying configuration changes.
- **Metabase filters:**
  - `[[AND {{visit_date}}]]` — field filter, bind to `emr_questionnaireresponse.created_date`.
  - `[[AND {{patient_name}}]]` — text filter, bind to `emr_patient.name`.
  - `[[AND zone = {{zone_filter}}]]` and `[[AND place_of_care = {{place_of_care}}]]` — exact-match filters applied on the resolved tag columns
- Results are ordered alphabetically by patient name.

*Last updated: 2026-07-07*
