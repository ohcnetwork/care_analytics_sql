# Total Patients Registered 

> Returns the count of registered patients with optional filtering by zone, frequency of visit, and cross-subsidy model

## Purpose

This query provides the total count of registered patients in Arike, allowing filtering by patient tags such as zone, frequency of visit, and cross-subsidy model.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `zone_filter` | TEXT | Filters by patient zone tag (parent_id: 55) | `Zone A` |
| `frequency_filter` | TEXT | Filters by frequency of visit tag (parent_id: 18) | `Weekly` |
| `cross_subsided_model_filter` | TEXT | Filters by cross-subsidy model tag (parent_id: 26) | `Fully supported` |



---

## Query

```sql
WITH patient_tags AS (
    SELECT
        ep.id AS patient_id,
        MAX(CASE WHEN et.parent_id = 55 THEN et.display END) AS zone,
        MAX(CASE WHEN et.parent_id = 18 THEN et.display END) AS frequency_of_visit,
        MAX(CASE WHEN et.parent_id = 26 THEN et.display END) AS cross_subsided_model
    FROM emr_patient ep
    LEFT JOIN LATERAL unnest(ep.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig et
        ON et.id = tag_id
       AND et.deleted = FALSE
       AND et.parent_id IN (55, 18, 26)
    WHERE ep.deleted = FALSE
    GROUP BY ep.id
)

SELECT COUNT(*) AS count
FROM emr_patient ep
LEFT JOIN patient_tags pt ON pt.patient_id = ep.id
WHERE ep.deleted = FALSE
--   [[AND (pt.zone) = ({{zone_filter}})]]
--   [[AND (pt.frequency_of_visit) = ({{frequency_filter}})]]
--   [[AND (pt.cross_subsided_model) = ({{cross_subsided_model_filter}})]];
```


## Drill-Down Query

Returns detailed patient information including demographics, identifiers, and all associated tags.

### Additional Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `patient_name` | TEXT | Filters by patient name | `'John'` |
| `alerts_filter` | TEXT | Filters by alert tags (parent_id: 47) | `JIC Box` |
| `special_note_filter` | TEXT | Filters by special note tags (parent_id: 22) | `Two staff required` |
| `others_filter` | TEXT | Filters by other specific tags (ids: 66, 67, 68) | `Collusion` |

```sql
WITH patient_tags AS (
    SELECT
        ep.id AS patient_id,
        MAX(CASE WHEN et.parent_id = 55 THEN et.display END) AS zone,
        MAX(CASE WHEN et.parent_id = 47 THEN et.display END) AS alerts,
        MAX(CASE WHEN et.parent_id = 18 THEN et.display END) AS frequency_of_care,
        MAX(CASE WHEN et.parent_id = 22 THEN et.display END) AS special_note,
        MAX(CASE WHEN et.parent_id = 26 THEN et.display END) AS cross_subsided_model,
        MAX(CASE WHEN et.id IN (66, 67, 68) THEN et.display END) AS others
    FROM emr_patient ep
    LEFT JOIN LATERAL unnest(ep.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig et 
        ON et.id = tag_id 
        AND et.deleted = FALSE
        AND (
            et.parent_id IN (55, 47, 18, 22, 26)
            OR et.id IN (66, 67, 68)
        )
    WHERE ep.deleted = FALSE
    GROUP BY ep.id
)

SELECT 
    ep.name,
    ep.phone_number,
    ep.year_of_birth,
    ep.gender,
    pi.value AS ADM,
    ep.created_date,
    pt.zone,
    pt.alerts,
    pt.others,
    pt.frequency_of_care,
    pt.special_note,
    pt.cross_subsided_model
FROM emr_patient ep
LEFT JOIN emr_patientidentifier pi 
    ON ep.id = pi.patient_id 
    AND pi.config_id = 2
LEFT JOIN patient_tags pt 
    ON pt.patient_id = ep.id
WHERE ep.deleted = FALSE
--   [[AND {{patient_name}}]]
--   [[AND (pt.zone) = ({{zone_filter}})]]
--   [[AND (pt.alerts) = ({{alerts_filter}})]]
--   [[AND (pt.frequency_of_care) = ({{frequency_filter}})]]
--   [[AND (pt.special_note) = ({{special_note_filter}})]]
--   [[AND (pt.cross_subsided_model) = ({{cross_subsided_model_filter}})]]
--   [[AND (pt.others) = ({{others_filter}})]]
ORDER BY ep.name ASC

```

## Notes

- Only non-deleted patients (`ep.deleted = FALSE`) and tags (`et.deleted = FALSE`) are included
- The query uses `LATERAL unnest()` to expand the `instance_tags` array for joining with tag configurations
- Hardcoded tag parent IDs:
  - `55`: Zone tags
  - `47`: Alert tags
  - `18`: Frequency of visit/care tags
  - `22`: Special note tags
  - `26`: Cross-subsidy model tags
  - Specific tag IDs `66, 67, 68`: Other classifications
- Patient identifier `config_id = 2` represents ADM (Admission Number)


*Last updated: 2025-12-17*
