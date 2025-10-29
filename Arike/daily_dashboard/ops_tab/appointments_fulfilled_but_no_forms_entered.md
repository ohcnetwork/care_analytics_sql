# KPI query to get the count of appointments fulfilled but no forms entered

```sql


WITH booking_dates AS (
    SELECT DISTINCT 
        DATE(emr_tokenslot.start_datetime) AS booking_date
    FROM emr_tokenbooking
    JOIN emr_tokenslot ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    WHERE emr_tokenbooking.status = 'fulfilled'
      [[AND {{created_date}}]]
),


extended_booking_dates AS (
    SELECT booking_date
    FROM booking_dates
    UNION ALL
    SELECT MAX(booking_date) + INTERVAL '1 day'
    FROM booking_dates
),


shifted_bookings AS (
    SELECT
        emr_tokenbooking.id AS booking_id,
        emr_tokenbooking.patient_id,
        emr_tokenbooking.associated_encounter_id,
        emr_tokenslot.start_datetime AS created_date,
        emr_patient.instance_tags,
        CASE
            WHEN emr_tokenslot.start_datetime::time >= '08:00:00' 
                 AND emr_tokenslot.start_datetime::time < '20:00:00'
                THEN 'day'
            ELSE 'night'
        END AS shift,
        CASE
            WHEN emr_tokenslot.start_datetime::time >= '00:00:00' 
                 AND emr_tokenslot.start_datetime::time < '08:00:00'
                THEN (emr_tokenslot.start_datetime::date - INTERVAL '1 day')
            ELSE emr_tokenslot.start_datetime::date
        END AS shift_date
    FROM emr_tokenbooking
    JOIN emr_tokenslot ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    JOIN emr_patient ON emr_tokenbooking.patient_id = emr_patient.id
    WHERE emr_tokenbooking.status = 'fulfilled'
      AND DATE(emr_tokenslot.start_datetime) IN (SELECT booking_date FROM extended_booking_dates)
      AND NOT (
          DATE(emr_tokenslot.start_datetime) = (SELECT MAX(booking_date) FROM extended_booking_dates)
          AND emr_tokenslot.start_datetime::time > '08:00:00'
      )
),


patient_tags AS (
    SELECT
        sb.patient_id,
        MAX(CASE WHEN et.parent_id = 55 THEN et.display END) AS zone,
        MAX(CASE WHEN et.parent_id = 18 THEN et.display END) AS frequency_of_visit,
        MAX(CASE WHEN et.parent_id = 26 THEN et.display END) AS cross_subsided_model
    FROM shifted_bookings sb
    LEFT JOIN LATERAL unnest(sb.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig et
        ON et.id = tag_id AND et.deleted = FALSE
       AND et.parent_id IN (55, 18, 26)
    GROUP BY sb.patient_id
)


SELECT COUNT(*) AS fulfilled_without_forms
FROM shifted_bookings sb
LEFT JOIN emr_questionnaireresponse qr 
    ON sb.associated_encounter_id = qr.encounter_id
LEFT JOIN patient_tags pt ON pt.patient_id = sb.patient_id
WHERE sb.shift_date IN (SELECT booking_date FROM extended_booking_dates)
  AND qr.id IS NULL

  [[AND LOWER(pt.zone) ILIKE LOWER({{zone_filter}})]]
  [[AND LOWER(pt.frequency_of_visit) ILIKE LOWER({{frequency_filter}})]]
  [[AND LOWER(pt.cross_subsided_model) ILIKE LOWER({{cross_subsided_model_filter}})]]
;

```

# Drill down to get the list of appointments fulfilled but no forms entered

```sql


WITH booking_dates AS (
    SELECT DISTINCT 
        DATE(emr_tokenslot.start_datetime) AS booking_date
    FROM emr_tokenbooking
    JOIN emr_tokenslot ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    WHERE emr_tokenbooking.status = 'fulfilled'
      [[AND {{created_date}}]]
),


extended_booking_dates AS (
    SELECT booking_date
    FROM booking_dates
    UNION ALL
    SELECT MAX(booking_date) + INTERVAL '1 day'
    FROM booking_dates
),


total_bookings AS (
    SELECT
        emr_patient.name AS patient_name,
        emr_patient.phone_number AS phone_number,
        emr_patient.gender AS gender,
        emr_patient.meta -> 'identifiers' -> 0 ->> 'value' AS adm,
        emr_patient.year_of_birth AS year_of_birth,
        emr_tokenslot.start_datetime AS init_date,
        CONCAT(users_user.first_name, ' ', users_user.last_name) AS staff_name,
        emr_tokenbooking.patient_id AS patient_id,
        emr_tokenbooking.tags AS tags,
        emr_tokenbooking.associated_encounter_id,
        emr_patient.instance_tags
    FROM emr_tokenbooking
    JOIN emr_tokenslot ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    JOIN emr_schedulableresource ON emr_tokenslot.resource_id = emr_schedulableresource.id
    JOIN users_user ON emr_tokenbooking.updated_by_id = users_user.id
    JOIN emr_patient ON emr_tokenbooking.patient_id = emr_patient.id
    WHERE emr_schedulableresource.facility_id = 2
      AND emr_tokenbooking.status = 'fulfilled'
      AND DATE(emr_tokenslot.start_datetime) IN (SELECT booking_date FROM extended_booking_dates)
      AND NOT (
          DATE(emr_tokenslot.start_datetime) = (SELECT MAX(booking_date) FROM extended_booking_dates)
          AND emr_tokenslot.start_datetime::time > '08:00:00'
      )
      [[AND {{staff_name}}]]
      [[AND {{patient_name}}]]
),


filtered_bookings AS (
    SELECT
        tb.patient_name,
        tb.phone_number,
        tb.gender,
        tb.adm,
        tb.year_of_birth,
        tb.init_date,
        tb.staff_name,
        tb.patient_id,
        tb.tags,
        tb.instance_tags,
        tb.init_date AS created_date,
        tb.associated_encounter_id,
        CASE
            WHEN tb.init_date::time >= '08:00:00' AND tb.init_date::time < '20:00:00' THEN 'day'
            ELSE 'night'
        END AS shift,
        CASE
            WHEN tb.init_date::time >= '00:00:00' AND tb.init_date::time < '08:00:00'
                THEN (tb.init_date::date - INTERVAL '1 day')
            ELSE tb.init_date::date
        END AS shift_date
    FROM total_bookings tb
),


patient_tags AS (
    SELECT
        fb.patient_id,
        MAX(CASE WHEN et.parent_id = 55 THEN et.display END) AS zone,
        MAX(CASE WHEN et.parent_id = 47 THEN et.display END) AS remarks,
        MAX(CASE WHEN et.parent_id = 18 THEN et.display END) AS frequency_of_visit,
        MAX(CASE WHEN et.parent_id = 22 THEN et.display END) AS special_note,
        MAX(CASE WHEN et.parent_id = 26 THEN et.display END) AS cross_subsided_model
    FROM filtered_bookings fb
    LEFT JOIN LATERAL unnest(fb.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig et 
        ON et.id = tag_id AND et.deleted = FALSE
    GROUP BY fb.patient_id
)


SELECT 
    fb.patient_name,
    fb.phone_number,
    fb.year_of_birth,
    fb.gender,
    fb.adm,
    fb.shift,
    fb.staff_name,
    fb.init_date,
    pt.zone,
    pt.remarks,
    pt.frequency_of_visit,
    pt.special_note,
    pt.cross_subsided_model
FROM filtered_bookings fb
LEFT JOIN emr_questionnaireresponse qr 
    ON fb.associated_encounter_id = qr.encounter_id
LEFT JOIN patient_tags pt 
    ON pt.patient_id = fb.patient_id
WHERE fb.shift_date IN (SELECT booking_date FROM extended_booking_dates)
  AND qr.id IS NULL  -- <<< Only show appointments with no forms

  [[AND LOWER(pt.zone) ILIKE LOWER({{zone_filter}})]]
  [[AND LOWER(pt.remarks) ILIKE LOWER({{remarks_filter}})]]
  [[AND LOWER(pt.frequency_of_visit) ILIKE LOWER({{frequency_filter}})]]
  [[AND LOWER(pt.special_note) ILIKE LOWER({{special_note_filter}})]]
  [[AND LOWER(pt.cross_subsided_model) ILIKE CONCAT('%', LOWER({{cross_subsided_model_filter}}), '%')]]

ORDER BY fb.patient_name;
