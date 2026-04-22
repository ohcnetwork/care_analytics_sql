
# Payment Reconciliation Report - SSMM

> Detailed list of payment reconciliations with invoice, patient, SSMM ID, and user details

## Purpose

Provides a comprehensive view of all payment reconciliation records along with the linked invoice number, patient details (including the SSMM patient identifier), payment metadata (amount, date, status, kind, method, type, issuer, credit-note flag), and the user who last updated the record.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filter by payment datetime range | `emr_paymentreconciliation.payment_datetime BETWEEN '2026-01-01' AND '2026-01-31'` |
| `status` | TEXT | Filter by reconciliation status | `emr_paymentreconciliation.status = 'completed'` |
| `method` | TEXT | Filter by payment method | `emr_paymentreconciliation.method = 'cash'` |
| `reconciliation_type` | TEXT | Filter by reconciliation type | `emr_paymentreconciliation.reconciliation_type = 'payment'` |
| `is_credit_note` | BOOLEAN | Filter for credit-note vs regular payments | `true` / `false` |
| `issuer_type` | TEXT | Filter by issuer type | `emr_paymentreconciliation.issuer_type = 'patient'` |
| `user_name` | TEXT | Filter by the full name of the user who updated the record | `'John Doe'` |

---

## Query

```sql
SELECT
    emr_invoice.number AS invoice_number,
    emr_patient.name AS patient_name,
    pi.value AS ssmm_id,
    emr_paymentreconciliation.amount,
    emr_paymentreconciliation.payment_datetime,
    emr_paymentreconciliation.status,
    emr_paymentreconciliation.kind,
    emr_paymentreconciliation.issuer_type,
    emr_paymentreconciliation.is_credit_note,
    emr_paymentreconciliation.method,
    emr_paymentreconciliation.reconciliation_type,
    TRIM(COALESCE(users_user.prefix || ' ', '') || users_user.first_name || ' ' || COALESCE(users_user.last_name, '')) AS updated_by
FROM emr_paymentreconciliation
JOIN users_user ON emr_paymentreconciliation.updated_by_id = users_user.id
LEFT JOIN emr_invoice ON emr_paymentreconciliation.target_invoice_id = emr_invoice.id
JOIN emr_account ON emr_paymentreconciliation.account_id = emr_account.id
JOIN emr_patient ON emr_account.patient_id = emr_patient.id
LEFT JOIN emr_patientidentifier pi
    ON emr_patient.id = pi.patient_id
   AND pi.config_id = 21
WHERE 1=1
  --[[AND {{date}}]]
  --[[AND {{status}}]]
  --[[AND {{method}}]]
  --[[AND {{reconciliation_type}}]]
  --[[AND emr_paymentreconciliation.is_credit_note = {{is_credit_note}}::boolean]]
  --[[AND {{issuer_type}}]]
  --[[AND TRIM(users_user.first_name || ' ' || COALESCE(users_user.last_name, '')) = {{user_name}}]]
ORDER BY emr_paymentreconciliation.payment_datetime DESC;
```


## Notes

- The patient identifier join is hardcoded to `pi.config_id = 21` which corresponds to the SSMM ID configuration — update this if the config ID changes.
- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- Results are ordered by most recent `payment_datetime` first.

*Last updated: 2026-04-20*

````
