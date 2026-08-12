
# Invoice Report - SSMM

> Detailed list of invoices with patient, SSMM ID, amount, status, and user details

## Purpose

Provides a comprehensive view of all invoice records along with the linked patient details (including the SSMM patient identifier), invoice metadata (gross amount, status, last modified date), and the user who last updated the record.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `DATE` | DATE | Filter by invoice modified date range | `emr_invoice.modified_date BETWEEN '2026-01-01' AND '2026-01-31'` |
| `Status` | TEXT | Filter by invoice status | `emr_invoice.status = 'issued'` |
| `user_name` | TEXT | Filter by the full name of the user who updated the record | `'John Doe'` |

---

## Query

```sql
SELECT
    emr_invoice.number AS invoice_number,
    emr_patient.name AS patient_name,
    pi.value AS ssmm_id,
    emr_invoice.total_gross,
    emr_invoice.status,
    emr_invoice.modified_date,
    TRIM(COALESCE(users_user.prefix || ' ', '') || users_user.first_name || ' ' || COALESCE(users_user.last_name, '')) AS updated_by
FROM emr_invoice
JOIN users_user ON emr_invoice.updated_by_id = users_user.id
JOIN emr_patient ON emr_invoice.patient_id = emr_patient.id
LEFT JOIN emr_patientidentifier pi
    ON emr_patient.id = pi.patient_id
   AND pi.config_id = 21
WHERE emr_invoice.deleted = FALSE
  --[[AND {{DATE}}]]
  --[[AND {{Status}}]]
  --[[AND TRIM(users_user.first_name || ' ' || COALESCE(users_user.last_name, '')) = {{user_name}}]]
ORDER BY emr_invoice.modified_date DESC;
```

## Notes

- Only active invoices are included (`emr_invoice.deleted = FALSE`).
- The patient identifier join is hardcoded to `pi.config_id = 21` which corresponds to the SSMM ID configuration — update this if the config ID changes.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards
- Results are ordered by most recent `modified_date` first.

*Last updated: 2026-04-22*

````
