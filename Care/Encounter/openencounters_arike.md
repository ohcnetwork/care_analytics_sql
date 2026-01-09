# Open Encounters List - Arike

> List of open (non-completed) encounters with patient details, staff information, and categorized tags

## Purpose

This query provides a comprehensive view of open patient encounters, including patient demographics, assigned nurse/doctor, and patient classification tags (zone, alerts, visit frequency, etc.). It's useful for monitoring active cases, managing patient visits, and tracking special care requirements in the Arike.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `staff_first_name` | TEXT | Filters by staff member's first name | `uu.first_name = 'John'` |
| `zone_filter` | TEXT | Filters by patient zone tag | `' Zone A'` |
| `alerts_filter` | TEXT | Filters by patient alerts tag | `'High Priority'` |
| `frequency_filter` | TEXT | Filters by frequency of visit tag | `'Weekly'` |
| `special_visit_filter` | TEXT | Filters by special visit tag | `'Home Visit'` |
| `cross_subsided_model_filter` | TEXT | Filters by cross-subsidized model tag | `'Subsidized'` |
| `Others_filter` | TEXT | Filters by other tags | `'Special Care'` |

---

## Query

```sql
WITH base_data AS (
    SELECT
        ep.id AS patient_id,
        ep.name AS patient_name,
        ep.gender,
        ep.phone_number,
        ep.year_of_birth,
        pi.value AS adm,
        uu.first_name || ' ' || uu.last_name AS nurse_doctor_name,
        ee.created_date,
        ep.instance_tags
    FROM emr_patient ep
    LEFT JOIN emr_encounter ee 
      ON ep.id = ee.patient_id
    LEFT JOIN users_user uu 
      ON ee.created_by_id = uu.id
    LEFT JOIN emr_patientidentifier pi
        ON pi.patient_id = ep.id AND pi.config_id = 2
    WHERE
      ee.status NOT IN ('completed', 'entered_in_error')
      AND ee.facility_id = 2
      AND ep.deleted = FALSE
      AND ee.deleted = FALSE
    --   [[AND {{staff_first_name}}]]  
),

patient_tags AS (
    SELECT
        bd.patient_id,
        MAX(CASE WHEN et.parent_id = 55 THEN et.display END) AS zone,
        MAX(CASE WHEN et.parent_id = 47 THEN et.display END) AS alerts,
        MAX(CASE WHEN et.parent_id = 18 THEN et.display END) AS frequency_of_visit,
        MAX(CASE WHEN et.parent_id = 22 THEN et.display END) AS special_visit,
        MAX(CASE WHEN et.parent_id = 26 THEN et.display END) AS cross_subsided_model,
        MAX(CASE WHEN et.id IN (66, 67, 68) THEN et.display END) AS others
    FROM base_data bd
    LEFT JOIN LATERAL unnest(bd.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig et
        ON et.id = tag_id
        AND et.deleted = FALSE
        AND et.parent_id IN (55, 47, 18, 22, 26)
    GROUP BY bd.patient_id
)

SELECT 
    bd.patient_name,
    bd.gender,
    bd.phone_number,
    bd.year_of_birth,
    bd.adm,
    bd.nurse_doctor_name,
    bd.created_date,
    pt.zone,
    pt.alerts,
    pt.others,
    pt.frequency_of_visit,
    pt.special_visit,
    pt.cross_subsided_model
FROM base_data bd
LEFT JOIN patient_tags pt ON pt.patient_id = bd.patient_id
WHERE 1=1
--   [[AND pt.zone = {{zone_filter}}]]
--   [[AND pt.alerts = {{alerts_filter}}]]
--   [[AND pt.frequency_of_visit = {{frequency_filter}}]]
--   [[AND pt.special_visit = {{special_visit_filter}}]]
--   [[AND pt.cross_subsided_model = {{cross_subsided_model_filter}}]]
--   [[AND pt.others = {{Others_filter}}]]
ORDER BY bd.created_date DESC;
```


## Notes

-  Query is filtered to `facility_id = 2` - update this value as needed
-  Uses `config_id = 2` for admission number - verify this matches your setup
- Only includes encounters that are NOT completed or entered_in_error (open encounters)
- Uses MAX aggregation with CASE statements to pivot tags into columns
- Results are ordered by encounter creation date (most recent first)

*Last updated: 2026-01-09*
