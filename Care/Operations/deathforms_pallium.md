# Death Forms

> Track the count of deceased patients registered in the system

## Purpose

Monitor and track deceased patients in the system. Provides aggregate count of patient deaths with optional filters by date, patient, and staff member who registered the death record.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filter by death registration date range | `2025-12-01 TO 2025-12-31` |
| `patient_name` | TEXT | Filter by specific patient | `John Doe` |
| `staff_name` | TEXT | Filter by staff member who registered death | `Jane Smith` |

---

## Query

```sql
SELECT 
    COUNT(DISTINCT ep.id) AS death_count
FROM emr_patient ep
LEFT JOIN users_user u ON ep.created_by_id = u.id
WHERE 
    ep.deceased_datetime IS NOT NULL
    --   [[AND {{date}}]]
    --   [[AND ep.name = {{patient_name}}]]
    --   [[AND TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) = {{staff_name}}]]
;
```


## Drill-Down Query

> Returns detailed information for each deceased patient, including demographics, staff attribution, and medical record number.

### Purpose

To provide a detailed list of deceased patients with their demographic and registration information, supporting death record tracking and review.

### Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filter by death registration date (optional) | `2025-12-01 TO 2025-12-31` |
| `patient_name` | TEXT | Filter by patient name (optional) | `John Doe` |
| `staff_name` | TEXT | Filter by staff full name (optional) | `Jane Smith` |

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
  LEFT JOIN emr_patientidentifier pi ON p.id = pi.patient_id
WHERE 
  pi.config_id = 5
  AND p.deceased_datetime IS NOT NULL
  --   [[AND {{date}}]]
  --   [[AND p.name = {{patient_name}}]]
  --   [[AND CONCAT(s.first_name, ' ', s.last_name) = {{staff_name}}]]
ORDER BY
  patient_name;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query filters for patients where `deceased_datetime IS NOT NULL` to identify deceased patients.
- The `config_id = 5` condition in the drill-down is used to select the correct Medical Record number (MRnumber) for each patient.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
