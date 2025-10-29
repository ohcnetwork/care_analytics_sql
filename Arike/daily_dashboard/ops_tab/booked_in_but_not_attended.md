# Kpi Query to get the count of appointments booked in but not attended

```sql

WITH booking_dates AS (
    SELECT DISTINCT 
        DATE(emr_tokenslot.start_datetime) AS booking_date
    FROM emr_tokenbooking
    JOIN emr_tokenslot ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    WHERE emr_tokenbooking.status = 'booked'
        [[AND {{created_date}}]]
),


extended_booking_dates AS (
    SELECT booking_date
    FROM booking_dates
    UNION
    SELECT MAX(booking_date) + INTERVAL '1 day'
    FROM booking_dates
),

shifted_bookings AS (
    SELECT
        emr_tokenbooking.id AS booking_id,
        emr_tokenbooking.patient_id,
        emr_patient.instance_tags,
        emr_tokenslot.start_datetime,
        CASE
            WHEN emr_tokenslot.start_datetime::time >= '08:00:00' 
                 AND emr_tokenslot.start_datetime::time < '20:00:00' THEN 'day'
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
    JOIN emr_schedulableresource ON emr_tokenslot.resource_id = emr_schedulableresource.id
    JOIN emr_patient ON emr_tokenbooking.patient_id = emr_patient.id
    WHERE emr_tokenbooking.status = 'booked'
      AND DATE(emr_tokenslot.start_datetime) IN (SELECT booking_date FROM extended_booking_dates)
      AND NOT (
          DATE(emr_tokenslot.start_datetime) = (SELECT MAX(booking_date) FROM extended_booking_dates)
          AND emr_tokenslot.start_datetime::time > '08:00:00'
      )
),

patient_tags AS (
    SELECT
        shifted_bookings.patient_id,
        MAX(CASE WHEN emr_tagconfig.parent_id = 55 THEN emr_tagconfig.display END) AS zone,
        MAX(CASE WHEN emr_tagconfig.parent_id = 18 THEN emr_tagconfig.display END) AS frequency_of_visit,
        MAX(CASE WHEN emr_tagconfig.parent_id = 26 THEN emr_tagconfig.display END) AS cross_subsided_model
    FROM shifted_bookings
    LEFT JOIN LATERAL unnest(shifted_bookings.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig 
        ON emr_tagconfig.id = tag_id
       AND emr_tagconfig.deleted = FALSE
       AND emr_tagconfig.parent_id IN (55, 18, 26)
    GROUP BY shifted_bookings.patient_id
)

SELECT COUNT(*) AS count
FROM shifted_bookings
LEFT JOIN patient_tags ON patient_tags.patient_id = shifted_bookings.patient_id
WHERE shifted_bookings.shift_date IN (SELECT booking_date FROM extended_booking_dates)
  [[AND (patient_tags.zone) ILIKE ({{zone_filter}})]]
  [[AND (patient_tags.frequency_of_visit) ILIKE ({{frequency_filter}})]]
  [[AND (patient_tags.cross_subsided_model) ILIKE CONCAT('%', ({{cross_subsided_model_filter}}), '%')]];


```

# Drill down query to get the list of Patients booked in but not attended

```sql


WITH booking_dates AS (
    SELECT DISTINCT 
        DATE(emr_tokenslot.start_datetime) AS booking_date
    FROM emr_tokenbooking
    JOIN emr_tokenslot ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    WHERE emr_tokenbooking.status = 'booked'
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
    users_user.first_name AS staff_first_name,  
    TRIM(practitioner_user.first_name || ' ' || COALESCE(practitioner_user.last_name, '')) AS practitioner,
    emr_tokenbooking.patient_id AS patient_id,
    emr_tokenbooking.tags AS tags,
    emr_patient.instance_tags
FROM emr_tokenbooking
JOIN emr_tokenslot ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
JOIN emr_schedulableresource ON emr_tokenslot.resource_id = emr_schedulableresource.id
JOIN users_user ON emr_tokenbooking.booked_by_id = users_user.id  
JOIN users_user AS practitioner_user ON emr_schedulableresource.user_id = practitioner_user.id  
JOIN emr_patient ON emr_tokenbooking.patient_id = emr_patient.id
WHERE emr_schedulableresource.facility_id = 2
  AND emr_tokenbooking.status = 'booked'
  AND DATE(emr_tokenslot.start_datetime) IN (SELECT booking_date FROM extended_booking_dates)
  AND NOT (
      DATE(emr_tokenslot.start_datetime) = (SELECT MAX(booking_date) FROM extended_booking_dates)
      AND emr_tokenslot.start_datetime::time > '08:00:00'
  )
  [[AND {{staff_first_name}}]]
  [[AND {{patient_name}}]]
),


filtered_bookings AS (
    SELECT
        total_bookings.*,
        CASE
            WHEN total_bookings.init_date::time >= '08:00:00' 
                 AND total_bookings.init_date::time < '20:00:00'
                THEN 'day'
            ELSE 'night'
        END AS shift,
        CASE
            WHEN total_bookings.init_date::time >= '00:00:00' 
                 AND total_bookings.init_date::time < '08:00:00'
                THEN (total_bookings.init_date::date - INTERVAL '1 day')
            ELSE total_bookings.init_date::date
        END AS shift_date
    FROM total_bookings
),


patient_tags AS (
    SELECT
        fb.patient_id,
        MAX(CASE WHEN et.parent_id = 55 THEN et.display END) AS zone,
        MAX(CASE WHEN et.parent_id = 47 THEN et.display END) AS remarks,
        MAX(CASE WHEN et.parent_id = 18 THEN et.display END) AS frequency_of_care,
        MAX(CASE WHEN et.parent_id = 22 THEN et.display END) AS special_note,
        MAX(CASE WHEN et.parent_id = 26 THEN et.display END) AS cross_subsided_model
    FROM filtered_bookings fb
    LEFT JOIN LATERAL unnest(fb.instance_tags) AS tag_id ON TRUE
    LEFT JOIN emr_tagconfig et 
        ON et.id = tag_id AND et.deleted = FALSE
    GROUP BY fb.patient_id
)


SELECT 
    filtered_bookings.patient_name,
    filtered_bookings.phone_number,
    filtered_bookings.year_of_birth,
    filtered_bookings.gender,
    filtered_bookings.adm, 
    filtered_bookings.shift,
    filtered_bookings.staff_first_name,
    filtered_bookings.practitioner,  
    filtered_bookings.init_date,
    patient_tags.zone,
    patient_tags.remarks,
    patient_tags.frequency_of_care,
    patient_tags.special_note,
    patient_tags.cross_subsided_model
FROM filtered_bookings
LEFT JOIN patient_tags 
    ON patient_tags.patient_id = filtered_bookings.patient_id
WHERE filtered_bookings.shift_date IN (SELECT booking_date FROM extended_booking_dates)

[[AND LOWER(patient_tags.zone) ILIKE LOWER({{zone_filter}})]]
[[AND LOWER(patient_tags.remarks) ILIKE LOWER({{remarks_filter}})]]
[[AND LOWER(patient_tags.frequency_of_care) ILIKE LOWER({{frequency_filter}})]]
[[AND LOWER(patient_tags.special_note) ILIKE LOWER({{special_note_filter}})]]
[[AND LOWER(patient_tags.cross_subsided_model) ILIKE CONCAT('%', LOWER({{cross_subsided_model_filter}}), '%')]]
ORDER BY filtered_bookings.patient_name;

```