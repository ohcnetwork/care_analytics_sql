# Patients Transferred to Secondary/NGO - Patient Care

> Track the count of patient care resource requests for patient transfers

## Purpose

Monitor and analyze the number of patient care resource requests for patients being transferred to secondary care or NGO facilities. Helps track care service allocation and transfer planning for patient care continuity.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `facility_id` | TEXT | Filter by facility external ID (optional) | `6909ac5e-37b5-4ff7-8311-65610685ed44` |
| `created_date` | DATE | Filter by request creation date range (optional) | `2025-12-01 TO 2025-12-31` |
| `staff_name` | TEXT | Filter by staff member who created request (optional) | `Jane Smith` |

---

## Query

```sql
SELECT
  COUNT(*)
FROM
  emr_resourcerequest
  JOIN emr_patient ON emr_resourcerequest.related_patient_id = emr_patient.id
  JOIN facility_facility ON emr_resourcerequest.origin_facility_id = facility_facility.id
  JOIN users_user ON emr_resourcerequest.created_by_id = users_user.id
WHERE
  emr_resourcerequest.category = 'patient_care'
  AND emr_resourcerequest.related_patient_id IS NOT NULL
  AND emr_resourcerequest.deleted = FALSE
  --   [[AND facility_facility.external_id::text = {{facility_id}}]]
  --   [[AND {{created_date}}]]
  --   [[AND (users_user.first_name || ' ' || users_user.last_name) = {{staff_name}}]]
;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query counts resource requests of category `'patient_care'` from the emr_resourcerequest table.
- Only requests with a valid related_patient_id are included using `emr_resourcerequest.related_patient_id IS NOT NULL`.
- Only non-deleted requests are included using `emr_resourcerequest.deleted = FALSE`.
- Facility filter uses `external_id::text` to match facility external identifiers and filters by origin facility.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
