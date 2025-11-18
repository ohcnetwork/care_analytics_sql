# KPI: Count of  Patients Registered

```sql 

SELECT COUNT(*) AS count
FROM emr_patient
WHERE deleted IS FALSE;

```


#  Drill down: List of  Patients Registered

```sql

SELECT
    p.name,
    p.phone_number,
    p.year_of_birth,
    p.gender,
    p.meta #> '{identifiers,0,value}' AS adm,
    p.created_date
FROM emr_patient p
WHERE p.deleted IS false
```