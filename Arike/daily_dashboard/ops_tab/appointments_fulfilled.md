# KPI query to get the count of appointments fulfilled

```sql

WITH booking_dates AS (
    SELECT DISTINCT 
        DATE(emr_tokenslot.start_datetime) AS booking_date
    FROM emr_tokenbooking
    JOIN emr_tokenslot ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    WHERE 1=1
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
        b.id AS booking_id,
        b.patient_id,
        p.instance_tags,
        t.start_datetime,
        CASE
            WHEN t.start_datetime::time >= '08:00:00' 
                 AND t.start_datetime::time < '20:00:00' THEN 'day'
            ELSE 'night'
        END AS shift,
        CASE
            WHEN t.start_datetime::time >= '00:00:00' 
                 AND t.start_datetime::time < '08:00:00'
                THEN (t.start_datetime::date - INTERVAL '1 day')
            ELSE t.start_datetime::date
        END AS shift_date
    FROM emr_tokenbooking b
    JOIN emr_tokenslot t ON b.token_slot_id = t.id
    JOIN emr_schedulableresource r ON t.resource_id = r.id
    JOIN emr_patient p ON b.patient_id = p.id
    JOIN users_user u ON b.booked_by_id = u.id
    WHERE r.facility_id = 2
      AND b.status = 'fulfilled'
      AND DATE(t.start_datetime) IN (SELECT booking_date FROM extended_booking_dates)
      AND NOT (
          DATE(t.start_datetime) = (SELECT MAX(booking_date) FROM extended_booking_dates)
          AND t.start_datetime::time > '08:00:00'
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
        ON et.id = tag_id
       AND et.deleted = FALSE
       AND et.parent_id IN (55, 18, 26)
    GROUP BY sb.patient_id
)

SELECT COUNT(*) AS count
FROM shifted_bookings sb
LEFT JOIN patient_tags pt ON pt.patient_id = sb.patient_id
WHERE sb.shift_date IN (SELECT booking_date FROM extended_booking_dates)

  [[AND LOWER(pt.zone) ILIKE LOWER({{zone_filter}})]]
  [[AND LOWER(pt.frequency_of_visit) ILIKE LOWER({{frequency_filter}})]]
  [[AND LOWER(pt.cross_subsided_model) ILIKE LOWER({{cross_subsided_model_filter}})]];

```

# Drill down query to get the list of appointments fulfilled

```sql


WITH booking_dates AS (
    SELECT DISTINCT 
        DATE(emr_tokenslot.start_datetime) AS booking_date
    FROM emr_tokenbooking
    JOIN emr_tokenslot ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    WHERE 1=1
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
        emr_patient.meta -> 'identifiers' -> 0 ->> 'value' AS adm, -- Corrected the aliasing of ADM
        emr_patient.year_of_birth AS year_of_birth,
        emr_tokenslot.start_datetime AS init_date,
        users_user.first_name AS staff_first_name,
        emr_tokenbooking.patient_id AS patient_id,
        emr_tokenbooking.tags AS tags,
		emr_patient.instance_tags
    FROM emr_tokenbooking
    JOIN emr_tokenslot ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    JOIN emr_schedulableresource ON emr_tokenslot.resource_id = emr_schedulableresource.id
    JOIN users_user ON emr_tokenbooking.booked_by_id = users_user.id
    JOIN emr_patient ON emr_tokenbooking.patient_id = emr_patient.id
    WHERE emr_schedulableresource.facility_id = 2
      AND emr_tokenbooking.status = 'fulfilled'
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
        total_bookings.patient_name,
        total_bookings.phone_number,
        total_bookings.gender,
        total_bookings.adm,  
        total_bookings.year_of_birth,
        total_bookings.init_date,
        total_bookings.staff_first_name,
        total_bookings.patient_id, 
        total_bookings.tags,   
		total_bookings.instance_tags,
		total_bookings.init_date as created_date,
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
    filtered_bookings.init_date,
	pt.zone,
    pt.remarks,
    pt.frequency_of_care,
    pt.special_note,
    pt.cross_subsided_model


FROM filtered_bookings
LEFT JOIN patient_tags pt 
  ON pt.patient_id = filtered_bookings.patient_id
WHERE filtered_bookings.shift_date IN (SELECT booking_date FROM extended_booking_dates)

[[AND LOWER(pt.zone) ILIKE LOWER({{zone_filter}})]]
  [[AND LOWER(pt.remarks) ILIKE LOWER({{remarks_filter}})]]
  [[AND LOWER(pt.frequency_of_care) ILIKE LOWER({{frequency_filter}})]]
  [[AND LOWER(pt.special_note) ILIKE LOWER({{special_note_filter}})]]
  [[AND LOWER(pt.cross_subsided_model) ILIKE CONCAT('%', LOWER({{cross_subsided_model_filter}}), '%') ]]

ORDER BY filtered_bookings.patient_name;

```