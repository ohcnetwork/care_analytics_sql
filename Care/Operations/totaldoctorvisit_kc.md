# Total Doctor Visit

> Track the total count of doctor visits recorded in the system

## Purpose

Monitor and analyze the total number of visits conducted by doctors based on questionnaire responses. Helps track visit volume  with optional filtering by facility, date, and staff member.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facility_id` | TEXT | Filter by facility external ID (optional) | `6909ac5e-37b5-4ff7-8311-65610685ed44` |
| `date` | DATE | Filter by visit date range (optional) | `2025-12-01 TO 2025-12-31` |
| `staff_name` | TEXT | Filter by staff member who conducted visit (optional) | `Jane Smith` |

---

## Query

```sql
SELECT 
    COUNT(DISTINCT emr_questionnaireresponse.id) AS nurse_visit_count
FROM emr_questionnaireresponse
JOIN emr_questionnaire 
    ON emr_questionnaire.id = emr_questionnaireresponse.questionnaire_id
JOIN users_user ON
     users_user.id = emr_questionnaireresponse.created_by_id
LEFT JOIN emr_encounter 
    ON emr_encounter.id = emr_questionnaireresponse.encounter_id
LEFT JOIN facility_facility 
    ON facility_facility.id = emr_encounter.facility_id
WHERE emr_questionnaire.id = 68
  AND emr_questionnaireresponse.deleted = FALSE
  --   [[AND facility_facility.external_id::text = {{facility_id}}]]
  --   [[AND {{date}}]]
  --   [[AND (users_user.first_name || ' ' || users_user.last_name) = {{staff_name}}]]
;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query counts distinct questionnaire responses, where each response represents a visit.
- Questionnaire_id = 68 identifies doctor visit forms and is instance-specific.
- Only non-deleted questionnaire responses are included using `emr_questionnaireresponse.deleted = FALSE`.
- Facility filter uses `external_id::text` to match facility external identifiers.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
