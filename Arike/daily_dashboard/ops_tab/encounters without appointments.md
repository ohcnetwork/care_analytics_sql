# KPI query to get the count of encounters without appointments

```sql

WITH encounter_dates AS (
    SELECT DISTINCT 
        DATE(created_date) AS encounter_date
    FROM emr_encounter
    WHERE 1=1
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
        e.patient_id,
        e.id AS encounter_id,
        e.created_date,
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
    WHERE e.appointment_id IS NULL
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

SELECT COUNT(DISTINCT se.encounter_id)
FROM shifted_encounters se
LEFT JOIN patient_tags pt ON pt.patient_id = se.patient_id
WHERE se.shift_date IN (SELECT encounter_date FROM extended_encounter_dates)
  [[AND LOWER(pt.zone) ILIKE LOWER({{zone_filter}})]]
  [[AND LOWER(pt.frequency_of_visit) ILIKE LOWER({{frequency_filter}})]]
  [[AND LOWER(pt.cross_subsided_model) ILIKE LOWER({{cross_subsided_model_filter}})]];

```

# Drill down query to list the encounters without appointment

```sql

WITH encounter_dates AS (
    SELECT DISTINCT 
        DATE(created_date) AS encounter_date
    FROM emr_encounter
    WHERE 1=1
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
    WHERE emr_encounter.appointment_id IS NULL
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
        shifted_encounters.patient_id,
        MAX(CASE WHEN emr_tagconfig.parent_id = 55 THEN emr_tagconfig.display END) AS zone,
        MAX(CASE WHEN emr_tagconfig.parent_id = 47 THEN emr_tagconfig.display END) AS remarks,
        MAX(CASE WHEN emr_tagconfig.parent_id = 18 THEN emr_tagconfig.display END) AS frequency_of_care,
        MAX(CASE WHEN emr_tagconfig.parent_id = 22 THEN emr_tagconfig.display END) AS special_note,
        MAX(CASE WHEN emr_tagconfig.parent_id = 26 THEN emr_tagconfig.display END) AS cross_subsided_model
    FROM shifted_encounters
    LEFT JOIN LATERAL unnest(shifted_encounters.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig 
        ON emr_tagconfig.id = tag_id AND emr_tagconfig.deleted = FALSE
    GROUP BY shifted_encounters.patient_id
)

SELECT 
    shifted_encounters.patient_name,
    shifted_encounters.phone_number,
    shifted_encounters.gender,
    shifted_encounters.year_of_birth,
    shifted_encounters.adm,
    shifted_encounters.staff_first_name,
    shifted_encounters.shift,
    shifted_encounters.created_date,
    patient_tags.zone,
    patient_tags.remarks,
    patient_tags.frequency_of_care,
    patient_tags.special_note,
    patient_tags.cross_subsided_model
FROM shifted_encounters
LEFT JOIN patient_tags 
  ON patient_tags.patient_id = shifted_encounters.patient_id
WHERE shifted_encounters.shift_date IN (SELECT encounter_date FROM extended_encounter_dates)
  [[AND LOWER(patient_tags.zone) ILIKE '%' || LOWER({{zone_filter}}) || '%']]
  [[AND LOWER(patient_tags.remarks) ILIKE '%' || LOWER({{remarks_filter}}) || '%']]
  [[AND LOWER(patient_tags.frequency_of_care) ILIKE '%' || LOWER({{frequency_filter}}) || '%']]
  [[AND LOWER(patient_tags.special_note) ILIKE '%' || LOWER({{special_note_filter}}) || '%']]
  [[AND LOWER(patient_tags.cross_subsided_model) ILIKE '%' || LOWER({{cross_subsided_model_filter}}) || '%']]
ORDER BY shifted_encounters.created_date, shifted_encounters.patient_name;

```