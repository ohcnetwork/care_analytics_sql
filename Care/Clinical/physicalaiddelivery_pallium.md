# Physical Aid Delivery

> Analyze the distribution of physical aids delivered to patients across the organization

## Purpose

Track and analyze the types of physical aids delivered to patients, including count of patients receiving each aid type.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filter by delivery date range | `2025-12-01 TO 2025-12-31` |
| `patient_name` | TEXT | Filter by specific patient | `John Doe` |
| `staff_name` | TEXT | Filter by staff member who delivered aid | `Jane Smith` |

---

## Query

```sql
SELECT
  aid.physical_aid,
  COUNT(DISTINCT qr.patient_id) AS patient_count
FROM emr_questionnaireresponse qr
JOIN emr_patient p ON qr.patient_id = p.id
JOIN users_user u ON qr.created_by_id = u.id
JOIN LATERAL (
  SELECT
    UPPER(TRIM(REPLACE(val ->> 'value', '_', ' '))) AS physical_aid
  FROM jsonb_array_elements(qr.responses) resp
    JOIN LATERAL jsonb_array_elements(resp -> 'values') val ON TRUE
  WHERE resp ->> 'question_id' = 'd78cee94-461d-46a8-98ac-f57b36584b1d'
) aid ON TRUE
WHERE qr.questionnaire_id = 18
--   [[AND {{date}}]]
--   [[AND p.name = {{patient_name}}]]
--   [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}}]]
GROUP BY aid.physical_aid
ORDER BY patient_count DESC, aid.physical_aid;
```


---

## Drill-Down Query

> Returns detailed patient information for each physical aid delivered, including staff, and delivery details.

### Purpose

To provide a detailed list of patients for each physical aid type, supporting patient-level review and aid delivery tracking.

### Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filter by delivery date (optional) | `2025-12-01 TO 2025-12-31` |
| `patient_name` | TEXT | Filter by patient name (optional) | `John Doe` |
| `staff_name` | TEXT | Filter by staff full name (optional) | `Jane Smith` |
| `physical_aid` | TEXT | Filter by physical aid type (optional) | `CRUTCHES` |

---

```sql
SELECT
  p.name AS patient_name,
  p.gender,
  EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
  p.phone_number,
  p.address,
  pi.value AS mrnumber,
  qr.created_date AS delivery_date,
  TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS staff_name,
  aid.physical_aid
FROM emr_questionnaireresponse qr
JOIN emr_patient p ON qr.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
JOIN users_user u ON qr.created_by_id = u.id
JOIN LATERAL (
  SELECT
    UPPER(TRIM(REPLACE(val ->> 'value', '_', ' '))) AS physical_aid
  FROM jsonb_array_elements(qr.responses) resp
    JOIN LATERAL jsonb_array_elements(resp -> 'values') val ON TRUE
  WHERE resp ->> 'question_id' = 'd78cee94-461d-46a8-98ac-f57b36584b1d'
) aid ON TRUE
WHERE qr.questionnaire_id = 18
--   [[AND {{date}}]]
--   [[AND p.name = {{patient_name}}]]
--   [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}}]]
--   [[AND aid.physical_aid ILIKE '%' || {{physical_aid}} || '%']]
ORDER BY delivery_date DESC, patient_name, aid.physical_aid;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query uses `questionnaire_id = 18` to identify Physical Aid Delivery forms.
- Specific question_id `d78cee94-461d-46a8-98ac-f57b36584b1d` is used to extract physical aid data.
- The `config_id = 5` condition is used to select the correct Medical Record number (mrnumber) for each patient.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
