# Patients on Opioids 

> Returns the count of patients on specific opioids, with optional filters for date, patient, and staff.

## Purpose

To analyze the number of patients administered specific opioids, supporting medication monitoring and pain management reporting.

## Parameters

| Parameter        | Type   | Description                                 | Example         |
|------------------|--------|---------------------------------------------|----------------|
| `created_date`   | DATE   | Filter by medication administration date (optional) | '2025-12-01'   |
| `patient_name`   | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`     | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

## Query

```sql
SELECT
	CASE
		WHEN ma.medication->>'display' ILIKE '%morphine%' THEN 'Morphine'
		WHEN ma.medication->>'display' ILIKE '%fentanyl%' THEN 'Fentanyl'
		WHEN ma.medication->>'display' ILIKE '%methadone%' THEN 'Methadone'
		WHEN ma.medication->>'display' ILIKE '%tramadol%' THEN 'Tramadol'
		ELSE 'Other'
	END AS medicine_name,
	COUNT(DISTINCT ma.patient_id) AS patient_count
FROM
	emr_medicationadministration ma
JOIN emr_patient p ON ma.patient_id = p.id
LEFT JOIN users_user u ON ma.created_by_id = u.id
WHERE
	ma.medication->>'display' ILIKE ANY (ARRAY[
		'%morphine%',
		'%fentanyl%',
		'%methadone%',
		'%tramadol%'
	])
	
		--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
		[[AND {{created_date}}]]
		[[AND p.name = {{patient_name}} ]]
		[[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}} ]]
	*/
GROUP BY
	medicine_name
ORDER BY
	patient_count DESC;
```


## Drill-Down Query

> Returns detailed patient and medication information for each opioid, including demographics, staff, and MR number.

### Purpose

To provide a detailed list of patients administered each opioid, supporting patient-level review and medication tracking.

### Parameters

| Parameter        | Type   | Description                                 | Example         |
|------------------|--------|---------------------------------------------|----------------|
| `created_date`   | DATE   | Filter by medication administration date (optional) | '2025-12-01'   |
| `medicine_name`  | TEXT   | Filter by opioid name (optional)            | 'Morphine'     |
| `patient_name`   | TEXT   | Filter by patient name (optional)           | 'John Doe'     |
| `staff_name`     | TEXT   | Filter by staff full name (optional)        | 'Jane Smith'   |

---

```sql
SELECT
	CASE
		WHEN m.medication->>'display' ILIKE '%morphine%' THEN 'Morphine'
		WHEN m.medication->>'display' ILIKE '%fentanyl%' THEN 'Fentanyl'
		WHEN m.medication->>'display' ILIKE '%methadone%' THEN 'Methadone'
		WHEN m.medication->>'display' ILIKE '%tramadol%' THEN 'Tramadol'
		ELSE 'Other'
	END AS medicine_name,
	p.name AS patient_name,
	p.gender,
	p.phone_number,
	EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
	p.address,
	pi.value AS MRnumber,
	TRIM(s.first_name || ' ' || COALESCE(s.last_name, '')) AS staff_name,
	m.created_date
FROM emr_medicationadministration m
JOIN emr_patient p ON m.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
LEFT JOIN users_user s ON m.created_by_id = s.id
WHERE
	m.medication->>'display' ILIKE ANY (ARRAY[
		'%morphine%',
		'%fentanyl%',
		'%methadone%',
		'%tramadol%'
	])
	
		--The following filters are Metabase-specific and will be replaced by Metabase if parameters are provided:
    /*
		[[AND  {{created_date}}]]
		[[AND CASE
				WHEN m.medication->>'display' ILIKE '%morphine%' THEN 'Morphine'
				WHEN m.medication->>'display' ILIKE '%fentanyl%' THEN 'Fentanyl'
				WHEN m.medication->>'display' ILIKE '%methadone%' THEN 'Methadone'
				WHEN m.medication->>'display' ILIKE '%tramadol%' THEN 'Tramadol'
				ELSE 'Other'
			END = {{medicine_name}} ]]
		[[AND p.name ={{patient_name}} ]]
		[[AND TRIM(s.first_name || ' ' || COALESCE(s.last_name, '')) ={{staff_name}} ]]
	*/
ORDER BY m.created_date DESC, patient_name;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The queries use medication display names to classify opioids.
- The `config_id = 5` condition is used to select the correct Medical Record number (MRnumber) for each patient.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-15*
