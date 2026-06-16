
# Appointment Booking Details - SSMM

> Detailed list of appointment bookings for a specific practitioner with patient, slot, schedule, and charge details

## Purpose

Returns a detailed booking view for a specific practitioner (`users_user.id`) at SSMM. Each row includes the slot start time, booking status, schedule name, charge item title and price, patient name with SSMM ID, the practitioner's name, and the availability JSON. 

## Parameters

The query currently uses a hardcoded `users_user.id = 247`. Update this value to look up bookings for a different practitioner, or convert it to a Metabase variable as needed.

---

## Query

```sql
SELECT
    emr_tokenslot.start_datetime AS slot_start_datetime,
    emr_tokenbooking.status AS tokenbooking_status,
    emr_schedule.name AS schedule_name,
    emr_chargeitem.title AS chargeitem_title,
    emr_chargeitem.total_price AS chargeitem_total_price,
    emr_patientidentifier.value AS ssmm_id,
    emr_patient.name AS patient_name,
    TRIM(users_user.first_name || ' ' || users_user.last_name) AS user_name,
    emr_availability.availability
FROM emr_tokenbooking
JOIN emr_tokenslot
  ON emr_tokenbooking.token_slot_id = emr_tokenslot.id
JOIN emr_availability
  ON emr_tokenslot.availability_id = emr_availability.id
JOIN emr_schedule
  ON emr_availability.schedule_id = emr_schedule.id
JOIN emr_schedulableresource
  ON emr_schedule.resource_id = emr_schedulableresource.id
JOIN users_user
  ON emr_schedulableresource.user_id = users_user.id
JOIN emr_patient
  ON emr_tokenbooking.patient_id = emr_patient.id
LEFT JOIN emr_patientidentifier
  ON emr_patient.id = emr_patientidentifier.patient_id
 AND emr_patientidentifier.config_id = 21
JOIN emr_chargeitem
  ON emr_tokenbooking.charge_item_id = emr_chargeitem.id
WHERE emr_schedulableresource.user_id = 247
AND emr_tokenslot.deleted = FALSE
AND emr_availability.deleted = FALSE
AND emr_schedule.deleted = FALSE
ORDER BY emr_schedule.name, emr_tokenslot.start_datetime;
```

## Notes

- `emr_schedulableresource.user_id = 247` is hardcoded — change this to target a different practitioner.
- The patient identifier join is hardcoded to `emr_patientidentifier.config_id = 21` which corresponds to the SSMM ID configuration — update this if the config ID changes.
- Results are ordered by schedule name then slot start time so all slots for the same schedule appear together chronologically.

*Last updated: 2026-06-16*
