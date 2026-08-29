
# Appointments Rescheduled More Than 5 Times 

> Patients who have had more than 5 rescheduled appointments at Arike, with reschedule details and zone

## Purpose

Identifies patients at Arike (`facility_id = 2`) whose appointments have been rescheduled more than 5 times in total. Each row is one rescheduled booking for such a patient, showing the patient details (name, phone, year of birth, gender, ADM, deceased status, zone), the booking note (reason), the staff who created the rescheduled booking, the slot start datetime, and the total reschedule count.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `start_datetime` | DATE / range | Metabase date filter (typically bound to `emr_tokenslot.start_datetime`) | `'2026-07-01'` |
| `patient_name` | TEXT | Metabase text filter (typically bound to `emr_patient.name`) | `'John Doe'` |
| `zone_filter` | TEXT | Filter by resolved zone tag display (exact match) | `'Zone A'` |

---

## Query

```sql
WITH rescheduled_bookings AS (
    SELECT
        emr_patient.id AS patient_id,
        emr_patient.name AS patient_name,
        emr_patient.phone_number,
        emr_patient.year_of_birth,
        emr_patient.gender,
        emr_tokenbooking.note AS reason,
        emr_patientidentifier.value AS adm,
        users_user.first_name || ' ' || users_user.last_name AS created_by_user,
        emr_tokenslot.start_datetime,
        CASE
            WHEN emr_patient.deceased_datetime IS NULL THEN 'No'
            ELSE 'Yes'
        END AS deceased,
        (
            SELECT COALESCE(MAX(emr_tagconfig.display), 'unassigned')
            FROM unnest(emr_patient.instance_tags) AS tag_id
            JOIN emr_tagconfig ON emr_tagconfig.id = tag_id
            WHERE emr_tagconfig.parent_id = 55
        ) AS zone
    FROM emr_tokenbooking
    JOIN emr_tokenslot
        ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
    JOIN emr_schedulableresource
        ON emr_tokenslot.resource_id = emr_schedulableresource.id
    JOIN emr_patient
        ON emr_tokenbooking.patient_id = emr_patient.id
    LEFT JOIN emr_patientidentifier
        ON emr_patient.id = emr_patientidentifier.patient_id
       AND emr_patientidentifier.config_id = 2
    JOIN users_user
        ON emr_tokenbooking.created_by_id = users_user.id
    WHERE emr_tokenbooking.status = 'rescheduled'
      AND LOWER(TRIM(emr_patient.name)) NOT LIKE '%test%'
      AND emr_schedulableresource.facility_id = 2
      --[[AND {{start_datetime}}]]
      --[[AND {{patient_name}}]]
),
patient_reschedule_count AS (
    SELECT
        patient_id,
        COUNT(*) AS reschedule_count
    FROM rescheduled_bookings
    GROUP BY patient_id
    HAVING COUNT(*) > 5
)
SELECT
    rb.patient_name,
    rb.phone_number,
    rb.year_of_birth,
    rb.gender,
    rb.reason,
    rb.adm,
    rb.created_by_user,
    rb.start_datetime,
    rb.deceased,
    prc.reschedule_count,
    rb.zone
FROM rescheduled_bookings rb
INNER JOIN patient_reschedule_count prc
    ON rb.patient_id = prc.patient_id
WHERE 1=1
    --[[AND rb.zone = {{zone_filter}}]]
ORDER BY rb.patient_name;
```

## Notes

- **Hardcoded IDs:**
  - `facility_id = 2` — Arike facility.
  - `emr_patientidentifier.config_id = 2` — ADM patient identifier configuration.
  - `parent_id = 55` — parent tag for **zone**.
  Update if the configuration changes.
- Results are ordered alphabetically by patient name.

*Last updated: 2026-07-15*
