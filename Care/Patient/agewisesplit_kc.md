# Age Wise Split

> Analyze patient distribution across age groups

## Purpose

Track and analyze the distribution of patients by age groups. Helps monitor patient demographics and identify age-based trends in the patient population.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facility_id` | TEXT | Filter by facility external ID (optional) | `6909ac5e-37b5-4ff7-8311-65610685ed44` |
| `date` | DATE | Filter by patient creation date range (optional) | `2025-12-01 TO 2025-12-31` |
| `staff_name` | TEXT | Filter by staff member who registered patient (optional) | `Jane Smith` |

---

## Query

```sql
SELECT
    CASE
        WHEN source.age BETWEEN 0  AND 18  THEN '0-18'
        WHEN source.age BETWEEN 19 AND 30  THEN '19-30'
        WHEN source.age BETWEEN 31 AND 40  THEN '31-40'
        WHEN source.age BETWEEN 41 AND 50  THEN '41-50'
        WHEN source.age BETWEEN 51 AND 60  THEN '51-60'
        WHEN source.age BETWEEN 61 AND 70  THEN '61-70'
        WHEN source.age BETWEEN 71 AND 80  THEN '71-80'
        WHEN source.age BETWEEN 81 AND 90  THEN '81-90'
        ELSE '91+'
    END AS age,
    COUNT(*) AS count
FROM (
    SELECT
        emr_patient.year_of_birth,
        date_part('year', CURRENT_DATE) - emr_patient.year_of_birth AS age,
        emr_patient.created_date::date
    FROM public.emr_patient 
    LEFT JOIN emr_encounter 
        ON emr_encounter.patient_id = emr_patient.id
    LEFT JOIN facility_facility 
        ON facility_facility.id = emr_encounter.facility_id
    LEFT JOIN users_user 
        ON users_user.id = emr_patient.created_by_id
    WHERE
        emr_patient.deceased_datetime IS NULL   
        --   [[AND facility_facility.external_id::text = {{facility_id}}]]
        --   [[AND {{date}}]]
        --   [[AND (users_user.first_name || ' ' || users_user.last_name) = {{staff_name}}]]
) AS source
GROUP BY 1, source.age
ORDER BY 
    CASE
        WHEN source.age BETWEEN 0  AND 18  THEN 1
        WHEN source.age BETWEEN 19 AND 30  THEN 2
        WHEN source.age BETWEEN 31 AND 40  THEN 3
        WHEN source.age BETWEEN 41 AND 50  THEN 4
        WHEN source.age BETWEEN 51 AND 60  THEN 5
        WHEN source.age BETWEEN 61 AND 70  THEN 6
        WHEN source.age BETWEEN 71 AND 80  THEN 7
        WHEN source.age BETWEEN 81 AND 90  THEN 8
        ELSE 9
    END;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- Age is calculated from `year_of_birth` using `date_part('year', CURRENT_DATE) - year_of_birth`.
- Filters out deceased patients using `emr_patient.deceased_datetime IS NULL`.
- The subquery calculates age, and the outer query groups by age ranges using CASE statements.
- Two CASE statements are used: one for grouping/display (`age` column), and another for ordering results numerically.
- Facility filter uses `external_id::text` to match facility external identifiers.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
