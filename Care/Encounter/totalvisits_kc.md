# Total Visits

> Track the total count of encounters/visits recorded in the system

## Purpose

Monitor and analyze the total number of encounters/visits across the organization. Helps track visit volume and trends with optional filtering by facility, date, and staff member.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facility_id` | TEXT | Filter by facility external ID (optional) | `6909ac5e-37b5-4ff7-8311-65610685ed44` |
| `created_date` | DATE | Filter by visit creation date range (optional) | `2025-12-01 TO 2025-12-31` |
| `staff_name` | TEXT | Filter by staff member who created visit (optional) | `Jane Smith` |

---

## Query

```sql
SELECT 
  COUNT(*) AS count
FROM 
  public.emr_encounter
JOIN 
  public.emr_patient
    ON emr_encounter.patient_id = emr_patient.id
LEFT JOIN facility_facility 
    ON facility_facility.id = emr_encounter.facility_id
LEFT JOIN users_user
  ON users_user.id = emr_encounter.created_by_id
  -- WHERE 1 = 1
  --   [[AND facility_facility.external_id::text = {{facility_id}}]]
  --   [[AND {{created_date}}]]
  --   [[AND (users_user.first_name || ' ' || users_user.last_name) = {{staff_name}}]]
;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query counts all encounters regardless of status or type.
- Facility filter uses `external_id::text` to match facility external identifiers.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
