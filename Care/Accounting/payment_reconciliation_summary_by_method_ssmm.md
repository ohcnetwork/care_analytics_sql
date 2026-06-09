
# Payment Reconciliation Summary by Method - SSMM

> Payment reconciliation summary with amounts split across payment methods

## Purpose

Aggregates active payment reconciliation records per invoice / patient / payment event and pivots the `amount` across the different payment methods (cash, credit card, debit card, cheque, DD, debit, etc.).

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filter by reconciliation modified date | `'2026-06-09'` |
| `ssmm_id` | TEXT | Filter by patient SSMM ID (exact match on `emr_patientidentifier.value`) | `'SSMM-1023'` |

---

## Query

```sql
SELECT
    emr_invoice.number AS invoice_number,
    emr_patient.name AS patient_name,
    pi.value AS ssmm_id,
    emr_paymentreconciliation.payment_datetime,
    emr_paymentreconciliation.status,
    emr_paymentreconciliation.kind,
    emr_paymentreconciliation.issuer_type,
    emr_paymentreconciliation.reconciliation_type,
    TRIM(COALESCE(users_user.prefix || ' ', '') || users_user.first_name || ' ' || users_user.last_name) AS updated_by,
    SUM(CASE WHEN emr_paymentreconciliation.method = 'cash' THEN emr_paymentreconciliation.amount ELSE 0 END) AS cash,
    SUM(CASE WHEN emr_paymentreconciliation.method = 'ccca' THEN emr_paymentreconciliation.amount ELSE 0 END) AS ccca,
    SUM(CASE WHEN emr_paymentreconciliation.method = 'cdac' THEN emr_paymentreconciliation.amount ELSE 0 END) AS cdac,
    SUM(CASE WHEN emr_paymentreconciliation.method = 'chck' THEN emr_paymentreconciliation.amount ELSE 0 END) AS chck,
    SUM(CASE WHEN emr_paymentreconciliation.method = 'ddpo' THEN emr_paymentreconciliation.amount ELSE 0 END) AS ddpo,
    SUM(CASE WHEN emr_paymentreconciliation.method = 'debc' THEN emr_paymentreconciliation.amount ELSE 0 END) AS debc
FROM emr_paymentreconciliation
JOIN users_user ON emr_paymentreconciliation.updated_by_id = users_user.id
LEFT JOIN emr_invoice ON emr_paymentreconciliation.target_invoice_id = emr_invoice.id
JOIN emr_account ON emr_paymentreconciliation.account_id = emr_account.id
JOIN emr_patient ON emr_account.patient_id = emr_patient.id
LEFT JOIN emr_patientidentifier pi
    ON emr_patient.id = pi.patient_id
   AND pi.config_id = 21
WHERE emr_paymentreconciliation.status = 'active'
AND emr_invoice.status NOT IN ('cancelled','enetered_in_error')
  --[[AND DATE(emr_paymentreconciliation.modified_date) = {{date}}]]
  --[[AND pi.value = {{ssmm_id}}]]
GROUP BY
    emr_invoice.number,
    emr_patient.name,
    pi.value,
    emr_paymentreconciliation.payment_datetime,
    emr_paymentreconciliation.status,
    emr_paymentreconciliation.kind,
    emr_paymentreconciliation.issuer_type,
    emr_paymentreconciliation.reconciliation_type,
    updated_by
ORDER BY emr_paymentreconciliation.payment_datetime DESC;
```

### Payment Method Codes

| Code | Description |
|------|-------------|
| `cash` | Cash |
| `ccca` | Credit Card |
| `cdac` | Credit / Debit Account |
| `chck` | Cheque |
| `ddpo` | Demand Draft / Postal Order |
| `debc` | Debit Card |

## Notes

- Only reconciliations with `status = 'active'` are included.
- The patient identifier join is hardcoded to `pi.config_id = 21` which corresponds to the SSMM ID configuration — update this if the config ID changes.
- **Metabase filters:**
  - `[[AND DATE(emr_paymentreconciliation.modified_date) = {{date}}]]` filters by the reconciliation's modified date.
  - `[[AND pi.value = {{ssmm_id}}]]` is an exact-match text filter on the SSMM patient ID.
- Results are ordered by most recent `payment_datetime` first.

*Last updated: 2026-06-09*
