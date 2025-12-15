# New Patient Registrations

> Returns the count of new patient registrations, with optional filters for date, patient name, and staff.

## Purpose

To track the number of new patients registered, supporting analysis by registration date, patient, or staff member.

## Parameters

| Parameter        | Type   | Description                                 | Example         |
|------------------|--------|---------------------------------------------|----------------|
| `created_date`   | DATE   | Filter by registration date (optional)      | '2025-12-01'   |
| `patient_name`   | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`     | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

## Query

```sql
SELECT COUNT(emr_patient.id) AS patient_count
FROM emr_patient
LEFT JOIN users_user s ON emr_patient.created_by_id = s.ID
WHERE emr_patient.deleted = FALSE

--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:

/*
  [[AND {{created_date}}]]
  [[AND emr_patient.name = {{patient_name}} ]]
  [[AND CONCAT(s.first_name, ' ', s.last_name) = {{staff_name}} ]]
*/
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The `deleted = FALSE` condition ensures only active patients are counted.
- Ensure `users_user` table and `created_by_id` are correctly mapped.
- All filters are optional and applied dynamically by Metabase.



---

## Drill-Down Query

> Returns detailed patient registration information, including demographics, staff, and MR number, for each new patient registration.

### Purpose

To provide a list of all newly registered patients with their demographic details, staff who registered them, and MR number, supporting further analysis and patient-level review.

### Parameters

| Parameter        | Type   | Description                                 | Example         |
|------------------|--------|---------------------------------------------|----------------|
| `created_date`   | DATE   | Filter by registration date (optional)      | '2025-12-01'   |
| `patient_name`   | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`     | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

```sql
SELECT
  p.name AS patient_name,
  p.gender,
  p.phone_number,
  EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
  p.address AS address,
  CONCAT(s.first_name, ' ', s.last_name) AS staff_name,
  p.created_date,
  pi.value AS MRnumber
FROM
  emr_patient p
  LEFT JOIN users_user s ON p.created_by_id = s.id
  LEFT JOIN emr_patientidentifier pi ON p.id = pi.patient_id AND pi.config_id = 5
WHERE 
  p.deleted=false
  /*
    The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    [[AND {{created_date}}]]
    [[AND p.name = {{patient_name}} ]]
    [[AND CONCAT(s.first_name, ' ', s.last_name) = {{staff_name}} ]]
  */
ORDER BY
  patient_name;
```

## Drill-Down Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The `pi.config_id = 5` condition ensures only relevant MR numbers are included.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-15*
