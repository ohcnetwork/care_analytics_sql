# Gender Split of Patients

> Returns the count of registered patients by gender group, with optional filters for date, patient name, and staff.

## Purpose

To analyze the gender distribution of registered patients, supporting demographic insights and gender-based reporting.

## Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `date`        | DATE   | Filter by registration date (optional)      | '2025-12-01'   |
| `patient_name`| TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`  | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

## Query

```sql
SELECT
  CASE 
    WHEN ep.gender IN ('Other') THEN 'Other'
    WHEN ep.gender = 'female' THEN 'female'
    WHEN ep.gender = 'male' THEN 'male'
  END AS gender_group,
  COUNT(DISTINCT ep.id) AS count
FROM
  emr_patient ep
LEFT JOIN users_user u ON ep.created_by_id = u.id
WHERE
  ep.deceased_datetime IS NULL
  AND ep.deleted = FALSE
 
    ---The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:

     /*
    [[AND {{date}}]]
    [[AND ep.name = {{patient_name}} ]]
    [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
    */
GROUP BY
  gender_group;
```


## Drill-Down Query

> Returns detailed patient information for each gender group, including demographics, MR number, staff, and registration date.

### Purpose

To provide a detailed list of patients in each gender group, supporting further demographic and patient-level analysis.

### Parameters

| Parameter        | Type   | Description                                 | Example         |
|------------------|--------|---------------------------------------------|----------------|
| `gender_group`   | TEXT   | Filter by gender group (optional)           | 'MALE'         |
| `date`          | DATE   | Filter by registration date (optional)      | '2025-12-01'   |
| `patient_name`  | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`    | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

```sql
SELECT
  p.name AS patient_name,
  p.gender,
  p.phone_number,
  EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
  p.address,
  pi.value AS MRnumber,
  TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS staff_name,
  p.created_date
FROM public.emr_patient p
LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
LEFT JOIN users_user u ON p.created_by_id = u.id
WHERE
  p.deceased_datetime IS NULL
  AND p.deleted = FALSE
  
    ---The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:

    /*
    [[AND p.gender = {{gender_group}}  ]]
    [[AND {{date}}]]
    [[AND p.name = {{patient_name}} ]]
    [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
    */
ORDER BY p.created_date DESC, patient_name;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The `pi.config_id = 5` condition ensures only relevant MR numbers are included.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-15*
