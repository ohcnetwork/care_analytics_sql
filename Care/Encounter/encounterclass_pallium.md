# Encounter Class

> Analyze the distribution of encounter types across the organization

## Purpose

Track and analyze the types of encounters recorded in the system, including count of encounters by class. Helps monitor encounter patterns and utilization across the care team.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created_date` | DATE | Filter by encounter creation date range | `2025-12-01 TO 2025-12-31` |
| `patient_name` | TEXT | Filter by specific patient | `John Doe` |
| `staff_name` | TEXT | Filter by staff member who created encounter | `Jane Smith` |

---

## Query

```sql
SELECT 
    ee.encounter_class,
    COUNT(*) AS encounter_count
FROM emr_encounter ee
JOIN emr_patient p ON ee.patient_id = p.id
LEFT JOIN users_user u ON ee.created_by_id = u.id
WHERE 
    ee.deleted = FALSE
    --   [[AND {{created_date}}]]
    --   [[AND p.name = {{patient_name}}]]
    --   [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}}]]
GROUP BY ee.encounter_class
ORDER BY ee.encounter_class;
```

### Output

| Column | Type | Description |
|--------|------|-------------|
| `encounter_class` | TEXT | Type/class of encounter |
| `encounter_count` | INTEGER | Number of encounters of this class |

---

## Drill-Down Query

> Returns detailed encounter information for each encounter class, including patient demographics, staff, and encounter status.

### Purpose

To provide a detailed list of individual encounters for each encounter class, supporting patient-level review and encounter tracking.

### Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created_date` | DATE | Filter by encounter creation date (optional) | `2025-12-01 TO 2025-12-31` |
| `encounter_class` | TEXT | Filter by encounter class type (optional) | `AMBULATORY` |
| `encounter_status` | TEXT | Filter by encounter status (optional) | `COMPLETED` |
| `patient_name` | TEXT | Filter by patient name (optional) | `John Doe` |
| `staff_name` | TEXT | Filter by staff full name (optional) | `Jane Smith` |

---

```sql
SELECT
    e.encounter_class,
    e.status,
    p.name AS patient_name,
    p.gender,
    p.phone_number,
    EXTRACT(YEAR FROM CURRENT_DATE) - p.year_of_birth AS age,
    p.address,
    pi.value AS MRnumber,
    TRIM(s.first_name || ' ' || COALESCE(s.last_name, '')) AS staff_name,
    e.created_date
FROM emr_encounter e
JOIN emr_patient p ON e.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON pi.patient_id = p.id AND pi.config_id = 5
LEFT JOIN users_user s ON e.created_by_id = s.id
WHERE
    e.deleted = FALSE
    --   [[AND {{created_date}}]]
    --   [[AND e.encounter_class = {{encounter_class}}]]
    --   [[AND e.status = {{encounter_status}}]]
    --   [[AND p.name = {{patient_name}}]]
    --   [[AND TRIM(s.first_name || ' ' || COALESCE(s.last_name, '')) = {{staff_name}}]]
ORDER BY e.created_date DESC, patient_name;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query filters only non-deleted encounters using `e.deleted = FALSE`.
- Encounter class represents the type of encounter (e.g., AMBULATORY, INPATIENT, etc.).
- The `config_id = 5` condition is used to select the correct Medical Record number (MRnumber) for each patient.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
