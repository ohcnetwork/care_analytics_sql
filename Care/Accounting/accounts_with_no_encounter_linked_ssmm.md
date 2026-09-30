# Accounts with No Encounter Linked - SSMM

> Patient accounts that have no primary encounter attached, with outstanding balance

## Purpose

Lists patient accounts where `primary_encounter_id` is not set, along with the patient's SSMM ID, account status, billing status, and due amount.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| *(none)* | - | Query runs as a static report with fixed filters | - |

---

## Query

```sql
SELECT
    emr_patient.name AS patient_name,
    emr_account.name AS account_name,
    ROUND(emr_account.total_balance)::integer AS due_amount,
    emr_account.status,
    pi.value AS ssmm_id,
    emr_account.billing_status
FROM emr_account
JOIN emr_patient
    ON emr_patient.id = emr_account.patient_id
LEFT JOIN emr_patientidentifier pi
    ON emr_patient.id = pi.patient_id
   AND pi.config_id = 21
WHERE emr_account.primary_encounter_id IS NULL
ORDER BY due_amount DESC;
```

## Notes

- **No encounter filter:** `emr_account.primary_encounter_id IS NULL` returns only accounts not linked to any primary encounter.
- **Due amount:** `total_balance` is rounded to the nearest whole number and cast to integer.
- Results are sorted by highest due amount first.

*Last updated: 2026-09-30*
