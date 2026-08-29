# Inpatient Encounters with Location

> Comprehensive view of inpatient encounters including patient details, bed assignments, and care team information

## Purpose

This query provides a complete overview of inpatient (IP) encounters, combining patient demographics, encounter creation details, bed assignments, and care team members. It's useful for tracking patient admissions, monitoring bed occupancy, and understanding care team composition across inpatient encounters.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `created_date` | DATE | Filters encounters by creation date | `DATE(created_date) = '2025-12-20'` |
| `patient_name` | TEXT | Filters by specific patient name | `'John Doe'` |
| `staff_name` | TEXT | Filters by staff member who created the encounter | `'Jane Smith'` |
| `care_team_role` | TEXT | Filters by specific care team role | `'Primary care physician'` |

---

## Query

```sql
WITH encounter_dates AS (
    SELECT DISTINCT 
        DATE(created_date) AS encounter_date
    FROM emr_encounter
    WHERE encounter_class = 'imp'
    --   [[AND {{created_date}}]]
),

encounters AS (
    SELECT
        emr_encounter.patient_id,
        emr_encounter.id AS encounter_id,
        emr_encounter.created_date,
        emr_encounter.care_team,
        emr_patient.name AS patient_name,
        emr_patient.phone_number,
        emr_patient.gender,
        emr_patient.address,
        TRIM(users_user.first_name || ' ' || COALESCE(users_user.last_name, '')) AS staff_name
    FROM emr_encounter
    JOIN emr_patient ON emr_encounter.patient_id = emr_patient.id
    JOIN users_user ON emr_encounter.created_by_id = users_user.id
    WHERE DATE(emr_encounter.created_date) IN (SELECT encounter_date FROM encounter_dates)
    --   [[AND emr_patient.name = {{patient_name}}]] 
    --   [[AND TRIM(users_user.first_name || ' ' || COALESCE(users_user.last_name, '')) = {{staff_name}}]]
),

bed_assignments AS (
    SELECT
        fle.encounter_id,
        fl.name AS bed_name,
        fle.created_date AS bed_assigned_date,
        TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS bed_assigned_by
    FROM emr_facilitylocationencounter fle
    JOIN emr_facilitylocation fl ON fle.location_id = fl.id
    LEFT JOIN users_user u ON fle.created_by_id = u.id
    WHERE fl.form = 'bd'
),

care_team_info AS (
    SELECT
        encounters.encounter_id,
        STRING_AGG(ct_elem -> 'role' ->> 'display', ', ' ORDER BY ct_elem -> 'role' ->> 'display') AS care_team_roles,
        STRING_AGG(TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')), ', ' ORDER BY u.first_name) AS care_team_users
    FROM encounters
    CROSS JOIN LATERAL jsonb_array_elements(encounters.care_team) AS ct_elem
    LEFT JOIN users_user u ON (ct_elem ->> 'user_id')::int = u.id
    WHERE jsonb_typeof(encounters.care_team) = 'array'
    GROUP BY encounters.encounter_id
)

SELECT 
    encounters.patient_name,
    encounters.phone_number,
    encounters.gender,
    encounters.address,
    encounters.staff_name,
    encounters.created_date,
    ba.bed_name,
    ba.bed_assigned_date,
    ba.bed_assigned_by,
    cti.care_team_roles AS care_team,
    cti.care_team_users AS username
FROM encounters
LEFT JOIN bed_assignments ba ON encounters.encounter_id = ba.encounter_id
LEFT JOIN care_team_info cti ON encounters.encounter_id = cti.encounter_id
-- WHERE 1=1
--   [[AND cti.care_team_roles = {{care_team_role}}]]
ORDER BY encounters.created_date, encounters.patient_name;
```


## Notes

- Query uses CTEs to organize logic into distinct stages: date filtering, encounter retrieval, bed assignments, and care team aggregation
- Only includes inpatient encounters (encounter_class = 'imp')
- The `care_team` field is stored as JSONB and is parsed to extract roles and user information
- Care team members are aggregated into comma-separated strings for roles and usernames
- Results are ordered by encounter creation date, then patient name
- Left joins ensure encounters are shown even if bed assignments or care team info is missing
- Bed assignments are filtered to only include beds (fl.form = 'bd')

*Last updated: 2025-12-20*
