
# Mobility Status Report by District 

> Count of patients per district by their latest mobility status (Bedbound / Homebound / Independently Active)

## Purpose

For each patient, find the **most recent** answer to the mobility-status question and pivot the counts by the patient's district. 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE / range | Metabase date filter (typically bound to `emr_questionnaireresponse.created_date`) | `'2026-06-01'` |

---

## Query

```sql
WITH latest_mobility AS (
  SELECT DISTINCT ON (emr_questionnaireresponse.patient_id)
    emr_questionnaireresponse.patient_id,
    emr_patient.organization_cache,
    rs -> 'values' -> 0 ->> 'value' AS mobility_value
  FROM emr_questionnaireresponse
  JOIN emr_patient
    ON emr_patient.id = emr_questionnaireresponse.patient_id
   
   AND emr_patient.deceased_datetime IS NULL
  CROSS JOIN LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS rs
  WHERE emr_questionnaireresponse.responses @> '[{"question_id": "e4b0d3f4-77fb-4fb6-9213-9c62fa6b5695"}]'::jsonb
    
    AND rs ->> 'question_id' = 'e4b0d3f4-77fb-4fb6-9213-9c62fa6b5695'
    --[[AND {{date}}]]
  ORDER BY emr_questionnaireresponse.patient_id, emr_questionnaireresponse.created_date DESC
)
SELECT
  emr_organization.name AS district_name,
  COUNT(*) FILTER (WHERE mobility_value ILIKE '%bedbound%')    AS "Bedbound",
  COUNT(*) FILTER (WHERE mobility_value ILIKE '%homebound%')   AS "Homebound",
  COUNT(*) FILTER (WHERE mobility_value ILIKE '%independent%') AS "Independently Active"
FROM latest_mobility
JOIN emr_organization
  ON emr_organization.id = ANY(latest_mobility.organization_cache)
 AND emr_organization.level_cache = 1
GROUP BY emr_organization.name
ORDER BY emr_organization.name;
```

## Notes

- **Metabase filter:** `[[AND {{date}}]]` is a field filter — bind it to `emr_questionnaireresponse.created_date` in the Metabase variable settings.
- Results are ordered alphabetically by `district_name`.

*Last updated: 2026-06-19*
