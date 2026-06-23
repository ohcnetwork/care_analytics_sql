# Diagnosis Counts by Condition

> Returns the count of patients by diagnosis, with optional filters for date, patient, and staff.

## Purpose

To analyze the distribution of diagnoses among patients, supporting clinical reporting and disease burden analysis.

## Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `date`        | DATE   | Filter by diagnosis date (optional)         | '2025-12-01'   |
| `patient_name`| TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`  | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

## Query

```sql
SELECT
	c.code #>> ARRAY['display'] AS diagnosis,
	COUNT(DISTINCT c.patient_id) AS count
FROM
	public.emr_condition c
JOIN public.emr_encounter e ON c.encounter_id = e.id
JOIN public.emr_patient p ON e.patient_id = p.id
LEFT JOIN public.users_user u ON c.created_by_id = u.id
WHERE 
	c.category IN ('encounter_diagnosis', 'chronic_condition')
	
		--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
		[[AND {{date}}]]
		[[AND p.name = {{patient_name}} ]]
		[[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
	*/
GROUP BY
	diagnosis
ORDER BY
	count DESC;
```


## Drill-Down Query

> Returns detailed patient information for each diagnosis, including demographics, staff, and MR number.

### Purpose

To provide a detailed list of patients for each diagnosis, supporting patient-level review and clinical follow-up.

### Parameters

| Parameter      | Type   | Description                                 | Example         |
|---------------|--------|---------------------------------------------|----------------|
| `date`        | DATE   | Filter by diagnosis date (optional)         | '2025-12-01'   |
| `patient_name`| TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`  | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |
| `diagnosis`   | TEXT   | Filter by diagnosis (optional)              | 'Diabetes'     |

---

```sql
SELECT
	cond.code #>> ARRAY['display'] AS diagnosis,
	p.name AS patient_name,
	p.gender,
	p.phone_number,
	EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
	p.address AS address,
	TRIM(s.first_name || ' ' || COALESCE(s.last_name, '')) AS staff_name,
	p.created_date,
	pi.value AS MRnumber
FROM
	public.emr_condition cond
JOIN public.emr_encounter e ON cond.encounter_id = e.id
JOIN public.emr_patient p ON e.patient_id = p.id
LEFT JOIN public.users_user s ON cond.created_by_id = s.id
LEFT JOIN public.emr_patientidentifier pi ON p.id = pi.patient_id AND pi.config_id = 5
WHERE
	p.deleted = false
	
		--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
		[[AND {{date}}]]
		[[AND p.name = {{patient_name}} ]]
		[[AND TRIM(s.first_name || ' ' || COALESCE(s.last_name, '')) = {{staff_name}} ]]
		[[AND cond.code #>> ARRAY['display'] = {{diagnosis}} ]]
	*/
ORDER BY
	patient_name;
```

## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The `config_id = 5` condition is used to select the correct Medical Record number (MRnumber) for each patient.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-15*
