# KPI Query: Registered But Not Visited Patient Count

```sql

SELECT COUNT(*) AS count
FROM emr_patient ep
WHERE ep.deleted IS FALSE
    AND NOT EXISTS (
        SELECT 1
        FROM emr_encounter ee
        WHERE ee.patient_id = ep.id
            AND ee.encounter_class = 'hh'
    );


```


# Drill down Query: Registered But Not Visited Patient Details

```sql

SELECT
    ep.id AS patient_id,
    ep.name,
    ep.phone_number,
    ep.year_of_birth,
    ep.gender,
    ep.meta #> '{identifiers,0,value}' AS adm,
    ep.created_date
FROM emr_patient ep
WHERE ep.deleted IS FALSE
    AND NOT EXISTS (
        SELECT 1
        FROM emr_encounter ee
        WHERE ee.patient_id = ep.id
            AND ee.encounter_class = 'hh'
    )
ORDER BY ep.created_date, ep.name;
```