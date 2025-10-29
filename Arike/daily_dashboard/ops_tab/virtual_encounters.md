# KPI query to get the count of virtual encounters

```sql

WITH encounter_dates AS (
    SELECT DISTINCT 
        DATE(created_date) AS encounter_date
    FROM emr_encounter
    WHERE encounter_class = 'vr'
      [[AND {{created_date}}]]
),


extended_encounter_dates AS (
    SELECT encounter_date
    FROM encounter_dates
    UNION ALL
    SELECT MAX(encounter_date) + INTERVAL '1 day'
    FROM encounter_dates
),

shifted_encounters AS (
    SELECT
        e.id AS encounter_id,
        e.created_date,
        e.patient_id,
        p.instance_tags,
        CASE
            WHEN e.created_date::time >= '08:00:00'
                 AND e.created_date::time < '18:00:00' THEN 'day'
            ELSE 'night'
        END AS shift,
        CASE
            WHEN e.created_date::time >= '00:00:00'
                 AND e.created_date::time < '08:00:00'
                THEN (e.created_date::date - INTERVAL '1 day')
            ELSE e.created_date::date
        END AS shift_date
    FROM emr_encounter e
    JOIN emr_patient p ON e.patient_id = p.id
    WHERE e.encounter_class = 'vr'
      AND DATE(e.created_date) IN (SELECT encounter_date FROM extended_encounter_dates)
      AND NOT (
          DATE(e.created_date) = (SELECT MAX(encounter_date) FROM extended_encounter_dates)
          AND e.created_date::time > '08:00:00'
      )
),

patient_tags AS (
    SELECT
        se.patient_id,
        MAX(CASE WHEN et.parent_id = 55 THEN et.display END) AS zone,
        MAX(CASE WHEN et.parent_id = 18 THEN et.display END) AS frequency_of_visit,
        MAX(CASE WHEN et.parent_id = 26 THEN et.display END) AS cross_subsided_model
    FROM shifted_encounters se
    LEFT JOIN LATERAL unnest(se.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig et
        ON et.id = tag_id
       AND et.deleted = FALSE
       AND et.parent_id IN (55, 18, 26)
    GROUP BY se.patient_id
)

SELECT 
    COUNT(*) AS count
FROM shifted_encounters se
LEFT JOIN patient_tags pt ON pt.patient_id = se.patient_id
WHERE se.shift_date IN (SELECT encounter_date FROM extended_encounter_dates)

  [[AND LOWER(pt.zone) ILIKE LOWER({{zone_filter}})]]
  [[AND LOWER(pt.frequency_of_visit) ILIKE LOWER({{frequency_filter}})]]
  [[AND LOWER(pt.cross_subsided_model) ILIKE LOWER({{cross_subsided_model_filter}})]];

```

# Drill down query to list patients with virtual encounter

```sql

WITH encounter_dates AS (
    SELECT DISTINCT 
        DATE(created_date) AS encounter_date
    FROM emr_encounter
    WHERE encounter_class = 'vr'
      [[AND {{created_date}}]]
),


extended_encounter_dates AS (
    SELECT encounter_date
    FROM encounter_dates
    UNION ALL
    SELECT MAX(encounter_date) + INTERVAL '1 day'
    FROM encounter_dates
),

shifted_encounters AS (
    SELECT
		emr_encounter.patient_id,
        emr_encounter.id AS encounter_id,
        emr_encounter.created_date,
        emr_patient.name AS patient_name,
        emr_patient.phone_number,
        emr_patient.gender,
        emr_patient.year_of_birth,
        (emr_patient.meta -> 'identifiers' -> 0 ->> 'value') AS adm,
        users_user.first_name AS staff_first_name,
		emr_patient.instance_tags,
        CASE
            WHEN emr_encounter.created_date::time >= '08:00:00'
                 AND emr_encounter.created_date::time < '18:00:00' THEN 'day'
            ELSE 'night'
        END AS shift,
        CASE
            WHEN emr_encounter.created_date::time >= '00:00:00'
                 AND emr_encounter.created_date::time < '08:00:00'
                THEN (emr_encounter.created_date::date - INTERVAL '1 day')
            ELSE emr_encounter.created_date::date
        END AS shift_date
    FROM emr_encounter
    JOIN emr_patient ON emr_encounter.patient_id = emr_patient.id
    JOIN users_user ON emr_encounter.created_by_id = users_user.id
    WHERE emr_encounter.encounter_class = 'vr'
      AND DATE(emr_encounter.created_date) IN (SELECT encounter_date FROM extended_encounter_dates)
      AND NOT (
          DATE(emr_encounter.created_date) = (SELECT MAX(encounter_date) FROM extended_encounter_dates)
          AND emr_encounter.created_date::time > '08:00:00'
      )
      [[AND {{staff_first_name}}]]
      [[AND {{patient_name}}]]
),


patient_tags AS (
    SELECT
        sp.patient_id,
        MAX(CASE WHEN et.parent_id = 55 THEN et.display END) AS zone,
        MAX(CASE WHEN et.parent_id = 47 THEN et.display END) AS remarks,
        MAX(CASE WHEN et.parent_id = 18 THEN et.display END) AS frequency_of_care,
        MAX(CASE WHEN et.parent_id = 22 THEN et.display END) AS special_note,
        MAX(CASE WHEN et.parent_id = 26 THEN et.display END) AS cross_subsided_model
    FROM shifted_encounters sp
    LEFT JOIN LATERAL unnest(sp.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig et 
        ON et.id = tag_id AND et.deleted = FALSE
    GROUP BY sp.patient_id
)

SELECT 
    se.patient_name,
    se.phone_number,
    se.gender,
    se.year_of_birth,
    se.adm,
    se.staff_first_name,
    se.shift,
    se.created_date,
	pt.zone,
    pt.remarks,
    pt.frequency_of_care,
    pt.special_note,
    pt.cross_subsided_model
	
FROM shifted_encounters se
LEFT JOIN patient_tags pt 
  ON pt.patient_id = se.patient_id
WHERE se.shift_date IN (SELECT encounter_date FROM extended_encounter_dates)
[[AND LOWER(pt.zone) ILIKE LOWER({{zone_filter}})]]
  [[AND LOWER(pt.remarks) ILIKE LOWER({{remarks_filter}})]]
  [[AND LOWER(pt.frequency_of_care) ILIKE LOWER({{frequency_filter}})]]
  [[AND LOWER(pt.special_note) ILIKE LOWER({{special_note_filter}})]]
  [[AND LOWER(pt.cross_subsided_model) ILIKE LOWER({{cross_subsided_model_filter}})]]

ORDER BY created_date, patient_name;

```