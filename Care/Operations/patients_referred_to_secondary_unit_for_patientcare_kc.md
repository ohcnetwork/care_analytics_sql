
# Patients Referred to Secondary Unit for Patient Care - KC

> Count of active (non-cancelled, non-rejected) resource requests in the `patient_care` category — i.e. patients referred to a secondary unit for patient care

## Purpose

Operational metric for KC showing how many patient-care resource requests have been raised by a facility (and optionally a specific staff member) in a given period. A "resource request" here represents a referral / request for patient-care services from one facility to another. 

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facility_id` | TEXT (UUID) | Filter by originating facility's external ID | `'a1b2c3d4-...'` |
| `created_date` | DATE / range | Metabase date filter (typically bound to `emr_resourcerequest.created_date`) | `'2026-06-01'` |
| `staff_name` | TEXT | Filter by the creating user's full name (`prefix + first + last`, trimmed) | `'Dr Asha Menon'` |

---

## Query

```sql
SELECT
  COUNT(*)
FROM
  emr_resourcerequest
  JOIN facility_facility ON emr_resourcerequest.origin_facility_id = facility_facility.id
  JOIN users_user ON emr_resourcerequest.created_by_id = users_user.id
WHERE
  emr_resourcerequest.category IN ('patient_care', 'PATIENT_CARE')
  AND emr_resourcerequest.status NOT IN ('cancelled', 'rejected')
  --[[AND facility_facility.external_id::text = {{facility_id}}]]
  --[[AND {{created_date}}]]
  --[[AND TRIM(COALESCE(users_user.prefix || ' ', '') || users_user.first_name || ' ' || COALESCE(users_user.last_name, '')) = {{staff_name}}]]
```


## Notes

- **Metabase filters:**
  - `[[AND {{created_date}}]]` is a field filter — bind it to `emr_resourcerequest.created_date` in the Metabase variable settings.
  - `{{facility_id}}` and `{{staff_name}}` are exact-match text filters.


*Last updated: 2026-06-01*

````

