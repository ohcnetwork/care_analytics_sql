# KPI CARD: Count of Open Encounters
 
 ```sql


SELECT COUNT(*) AS patient_count
FROM public.emr_patient ep
LEFT JOIN public.emr_encounter ee
    ON ep.id = ee.patient_id
    AND ee.facility_id = 2
    AND ee.deleted IS FALSE
    AND ee.status <> 'completed'
    AND ee.status <> 'entered_in_error'
WHERE ep.deleted IS FALSE;

```

# Drilldown Query: List of Open Encounters

```sql

SELECT
    ep.name AS patient_name,
    ep.gender,
    ep.phone_number,
    ep.year_of_birth,
    ep.meta #> '{identifiers,0,value}' AS adm,
    uu.first_name || ' ' || uu.last_name AS nurse_doctor_name,
    ee.created_date
FROM public.emr_patient ep
LEFT JOIN public.emr_encounter ee
    ON ep.id = ee.patient_id
    AND ee.facility_id = 2
    AND ee.deleted IS FALSE
    AND ee.status NOT IN ('completed', 'entered_in_error')
LEFT JOIN public.users_user uu
    ON ee.created_by_id = uu.id
WHERE ep.deleted IS FALSE
ORDER BY ee.created_date DESC;

```