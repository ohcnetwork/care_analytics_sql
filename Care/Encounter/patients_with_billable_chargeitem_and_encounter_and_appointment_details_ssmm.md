
# Patients with Billable Charge Item and Encounter/Appointment Details - SSMM

> Patient-level list of encounters linked to appointments that have billable charge items 

## Purpose

Returns encounter records at SSMM where the linked appointment (`emr_tokenbooking`) has a charge item in `billable` status. The result includes patient details, SSMM identifier, encounter and appointment statuses, charge item status/value, and encounter date.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date_filter` | DATE / range | Metabase date filter (typically bound to `emr_encounter.created_date`) | `'2026-08-01'` |
| `encounter_class` | TEXT | Filter by encounter class (exact match on `emr_encounter.encounter_class`) | `'amb'` |
| `encounter_status` | TEXT | Filter by encounter status (exact match on `emr_encounter.status`) | `'in-progress'` |
| `ssmm_id` | TEXT | Filter by patient SSMM identifier value (exact match on `emr_patientidentifier.value`) | `'SSMM-100245'` |

---

## Query

```sql
SELECT
	emr_patient.name AS patient_name,
	emr_patientidentifier.value AS ssmm_id,
	emr_encounter.status AS encounter_status,
	emr_encounter.encounter_class AS encounter_class,
	emr_tokenbooking.status AS appointment_status,
	emr_chargeitem.status AS charge_item_status,
	emr_chargeitem.total_price AS total_price,
	emr_encounter.created_date AS encounter_date
FROM emr_encounter
JOIN emr_patient
	ON emr_patient.id = emr_encounter.patient_id
LEFT JOIN emr_patientidentifier
	ON emr_patientidentifier.patient_id = emr_patient.id
   AND emr_patientidentifier.config_id = 21
JOIN emr_tokenbooking
	ON emr_tokenbooking.associated_encounter_id = emr_encounter.id
JOIN emr_chargeitem
	ON emr_chargeitem.id = emr_tokenbooking.charge_item_id
WHERE emr_chargeitem.status = 'billable'
  AND emr_chargeitem.total_price > 0
  --[[AND {{date_filter}}]]
  --[[AND {{encounter_class}}]]
  --[[AND {{encounter_status}}]]
  --[[AND emr_patientidentifier.value = {{ssmm_id}}]]
ORDER BY emr_encounter.created_date DESC, emr_patient.name;
```

## Notes

- **Core cohort:** Only rows where `emr_chargeitem.status = 'billable'` and `total_price > 0` are included.
- **Identifier mapping:** `config_id = 21` is hardcoded for SSMM patient identifier configuration; update if this mapping changes.

*Last updated: 2026-08-13*
