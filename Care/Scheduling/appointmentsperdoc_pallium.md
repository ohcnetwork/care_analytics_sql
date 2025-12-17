# Appointments per Doctor

> Returns the total number of appointments per doctor, with optional filters for appointment date, doctor, and patient.

## Purpose

To analyze the appointment load per doctor, performance tracking and patient access insights.

## Parameters

| Parameter           | Type   | Description                                 | Example         |
|---------------------|--------|---------------------------------------------|----------------|
| `appointment_date`  | DATE   | Filter by appointment date (optional)       | '2025-12-01'   |
| `doctor_name`       | TEXT   | Filter by doctor full name (optional)       | 'Dr. Smith'    |
| `patient_name`      | TEXT   | Filter by patient name (optional)           | 'John Doe'     |

---

## Query

```sql
WITH doctor_bookings AS (
    SELECT 
        emr_schedulableresource.user_id,
        emr_tokenbooking.id AS booking_id,
        emr_tokenbooking.patient_id,
        emr_tokenslot.start_datetime
    FROM emr_tokenbooking
    JOIN emr_tokenslot ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    JOIN emr_schedulableresource ON emr_tokenslot.resource_id = emr_schedulableresource.id
    JOIN users_user ON emr_schedulableresource.user_id = users_user.id
    WHERE users_user.user_type = 'doctor'
      
       ---The following filter is Metabase-specific and will be replaced by Metabase if parameters are provided:
       /*
        [[AND {{appointment_date}}]]
      */
)

SELECT 
    TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS doctor_name,
    COUNT(db.booking_id) AS total_appointments
FROM doctor_bookings db
JOIN users_user u ON db.user_id = u.id
JOIN emr_patient p ON db.patient_id = p.id

  ---The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
  /*
  [[WHERE TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{doctor_name}} ]]
  [[AND p.name = {{patient_name}} ]]
*/
GROUP BY db.user_id, doctor_name
ORDER BY total_appointments DESC;
```


## Drill-Down Query

> Returns detailed patient and appointment information for each doctor, MR number, and appointment date.

### Purpose

To provide a detailed list of patients and their appointment details for each doctor, supporting further analysis and patient-level review.

### Parameters

| Parameter           | Type   | Description                                 | Example         |
|---------------------|--------|---------------------------------------------|----------------|
| `appointment_date`  | DATE   | Filter by appointment date (optional)       | '2025-12-01'   |
| `patient_name`      | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `Doctor`            | TEXT   | Filter by doctor full name (optional)       | 'Dr. Smith'    |

---

```sql
SELECT
    p.name AS patient_name,
    p.gender,
    p.phone_number,
    EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
    p.address,
    pi.value AS MRnumber,
    TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS doctor_name,
    b.created_date AS booking_created_date
FROM emr_tokenbooking b
JOIN emr_tokenslot ts ON b.token_slot_id = ts.id
JOIN emr_schedulableresource sr ON ts.resource_id = sr.id
JOIN users_user u ON sr.user_id = u.id AND u.user_type = 'doctor'
JOIN emr_patient p ON b.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
---The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
/*
WHERE 1=1
    [[AND {{appointment_date}} ]]
    [[AND p.name = {{patient_name}} ]]
    [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{Doctor}} ]]
  */
ORDER BY b.created_date DESC, patient_name;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The `pi.config_id = 5` condition ensures only relevant MR numbers are included.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-15*
