
# JIC box Tag Issued Patients 

> Patients tagged with the JIC box tag, including ADM identifier, zone, and deceased status

## Purpose

Lists patients at Arike who carry the **JIC** box tag (`tag_id = 68`) along with their ADM identifier, contact details, deceased status, and zone.

---

## Query

```sql
SELECT
    emr_patient.name,
    emr_patient.phone_number,
    emr_patient.year_of_birth,
    emr_patient.gender,
    pi.value AS ADM,
    emr_patient.created_date,
    CASE
        WHEN emr_patient.deceased_datetime IS NULL THEN 'No'
        ELSE 'Yes'
    END AS deceased,
    COALESCE(
        (SELECT et.display
         FROM unnest(emr_patient.instance_tags) AS tag_id
         LEFT JOIN emr_tagconfig et ON et.id = tag_id
         WHERE et.parent_id = 55),
        'unassigned'
    ) AS zone
FROM emr_patient
LEFT JOIN emr_patientidentifier pi
    ON emr_patient.id = pi.patient_id
   AND pi.config_id = 2
LEFT JOIN LATERAL unnest(emr_patient.instance_tags) AS tag_id ON TRUE
WHERE tag_id = 68
ORDER BY emr_patient.name ASC;
```

## Notes

- Results are ordered alphabetically by patient name.

*Last updated: 2026-07-06*
