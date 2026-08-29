# Latest Diagnosis

> Analyze diagnosis distribution from the latest patient encounters

## Purpose

Track and analyze the distribution of diagnoses recorded in the most recent encounter for each patient. Helps monitor current health conditions and treatment patterns across the organization.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filter by encounter date range (optional) | `2025-12-01 TO 2025-12-31` |
| `facility_id` | TEXT | Filter by facility external ID (optional) | `6909ac5e-37b5-4ff7-8311-65610685ed44` |
| `staff_name` | TEXT | Filter by staff member who recorded diagnosis (optional) | `Jane Smith` |

---

## Query

```sql
WITH encounters_with_diagnosis AS (
  SELECT
    public.emr_encounter.id AS encounter_id,
    public.emr_encounter.patient_id,
    public.emr_encounter.created_date,
    public.emr_encounter.facility_id,
    public.emr_condition.created_by_id AS staff_id
  FROM public.emr_encounter
  JOIN public.emr_condition 
    ON public.emr_condition.encounter_id = public.emr_encounter.id
  WHERE 
    public.emr_condition.category in ('encounter_diagnosis', 'chronic_condition')
    --   [[AND {{date}}]]
),
latest_encounter AS (
  SELECT DISTINCT ON (patient_id)
    encounter_id,
    patient_id,
    created_date AS latest_encounter_date,
    facility_id,
    staff_id
  FROM encounters_with_diagnosis
  ORDER BY patient_id, created_date DESC
)
SELECT
  public.emr_condition.code #>> ARRAY['display'] AS diagnosis,
  COUNT(DISTINCT public.emr_condition.patient_id) AS count
FROM
  latest_encounter
  JOIN public.emr_condition 
    ON public.emr_condition.encounter_id = latest_encounter.encounter_id
  JOIN public.facility_facility 
    ON public.facility_facility.id = latest_encounter.facility_id
  LEFT JOIN public.users_user
    ON public.users_user.id = latest_encounter.staff_id
  --   WHERE 1=1
  --   [[AND public.facility_facility.external_id::text = {{facility_id}}]]
  --   [[AND (users_user.first_name || ' ' || users_user.last_name) = {{staff_name}}]]
GROUP BY
  diagnosis
ORDER BY
  count DESC;
```


## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query uses two CTEs: `encounters_with_diagnosis` identifies all encounters with diagnoses, and `latest_encounter` selects the most recent encounter per patient.
- Uses `DISTINCT ON (patient_id)` to select the latest encounter per patient, ordered by `created_date DESC`.
- Diagnosis categories are filtered to include only `'encounter_diagnosis'` and `'chronic_condition'` types.
- Facility filter uses `external_id::text` to match facility external identifiers.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
