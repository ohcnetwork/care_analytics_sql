# KPI Query: Count of patients registered but no care given

```sql

SELECT COUNT(*) AS "count"
FROM public.emr_patient ep
LEFT JOIN public.emr_encounter ee
    ON ep.id = ee.patient_id
WHERE (ee.status <> 'entered_in_error' OR ee.status IS NULL)
    AND ee.id IS NULL
    AND (ee.encounter_class <> 'vr' OR ee.encounter_class IS NULL);

```


# Drill down query: List of patients registered but no care given

```sql 

SELECT
    ep.id AS patient_id,
    ep.name AS patient_name,
    ep.gender,
    ep.phone_number,
    ep.year_of_birth,
    ep.meta #> '{identifiers,0,value}' AS adm,
    ep.created_date
FROM public.emr_patient ep
LEFT JOIN public.emr_encounter ee
    ON ep.id = ee.patient_id
WHERE ep.deleted IS FALSE
    AND (ee.status <> 'entered_in_error' OR ee.status IS NULL)
    AND ee.id IS NULL
    AND (ee.encounter_class <> 'vr' OR ee.encounter_class IS NULL)
ORDER BY ep.created_date DESC;


```