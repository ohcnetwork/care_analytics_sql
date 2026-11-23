
# Reception Counter Report with IP/OP Split - SSMM

> Per-staff counter summary of invoiced amounts, payments collected, refund invoices and credit notes, split into IP, OP and Total

## Purpose

Counter/shift reconciliation for SSMM reception staff. For a selected staff member (and optionally a date), shows how much they invoiced vs. how much they collected, broken down by whether the billing account belongs to an in-patient (IP) or out-patient (OP) visit, so cash-counter closing can be checked against the system.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `staff_external_id` | TEXT (UUID) | **Required.** External ID of the staff user | `'a1b2c3d4-...'` |
| `date` | DATE | Optional. Invoice last-modified date / payment date (IST) | `'2026-11-23'` |

---

## Query

```sql
WITH inv AS (
    SELECT
        CASE WHEN ae.encounter_class = 'imp' THEN 'IP' ELSE 'OP' END AS visit_type,
        COALESCE(SUM(i.total_gross) FILTER (WHERE i.is_refund = FALSE), 0) AS invoiced,
        COALESCE(SUM(i.total_gross) FILTER (WHERE i.is_refund = TRUE), 0)  AS refunds
    FROM emr_invoice i
    LEFT JOIN emr_account a    ON a.id = i.account_id
    LEFT JOIN emr_encounter ae ON ae.id = a.primary_encounter_id
    JOIN users_user u          ON u.id = i.updated_by_id
    WHERE i.deleted = FALSE
      AND i.status NOT IN ('cancelled', 'entered_in_error')
    --   [[AND (i.modified_date AT TIME ZONE 'Asia/Kolkata')::date = {{date}}]]
    --   AND u.external_id = {{staff_external_id}}::uuid
    GROUP BY 1
),
pay AS (
    SELECT
        CASE WHEN ae.encounter_class = 'imp' THEN 'IP' ELSE 'OP' END AS visit_type,
        COALESCE(SUM(pr.amount) FILTER (WHERE pr.is_credit_note = FALSE), 0) AS collected,
        COALESCE(SUM(pr.amount) FILTER (WHERE pr.is_credit_note = TRUE), 0)  AS credit_notes
    FROM emr_paymentreconciliation pr
    LEFT JOIN emr_account a    ON a.id = pr.account_id
    LEFT JOIN emr_encounter ae ON ae.id = a.primary_encounter_id
    JOIN users_user u          ON u.id = pr.created_by_id
    WHERE pr.deleted = FALSE
      AND pr.status = 'active'
      AND pr.outcome = 'complete'
    --   [[AND (pr.payment_datetime AT TIME ZONE 'Asia/Kolkata')::date = {{date}}]]
    --   AND u.external_id = {{staff_external_id}}::uuid
    GROUP BY 1
),
types(visit_type, ord) AS (
    VALUES ('IP', 1), ('OP', 2)
),
res AS (
    SELECT
        t.ord,
        t.visit_type,
        COALESCE(inv.invoiced, 0)      AS invoiced,
        COALESCE(pay.collected, 0)     AS collected,
        COALESCE(inv.refunds, 0)       AS refunds,
        COALESCE(pay.credit_notes, 0)  AS credit_notes
    FROM types t
    LEFT JOIN inv ON inv.visit_type = t.visit_type
    LEFT JOIN pay ON pay.visit_type = t.visit_type
)
SELECT
    visit_type,
    ROUND(invoiced, 2)             AS invoiced_gross,
    ROUND(collected, 2)            AS payments_collected,
    ROUND(invoiced - collected, 2) AS difference,
    ROUND(refunds, 2)              AS refund_invoices,
    ROUND(credit_notes, 2)         AS credit_notes
FROM (
    SELECT ord, visit_type, invoiced, collected, refunds, credit_notes FROM res
    UNION ALL
    SELECT 3, 'Total', SUM(invoiced), SUM(collected), SUM(refunds), SUM(credit_notes) FROM res
) x
ORDER BY ord;
```


## Notes

- **IP/OP split** is based on the account's primary encounter (`emr_account.primary_encounter_id`). `encounter_class = 'imp'` is IP. Everything else is OP, **including accounts with no primary encounter**.
- **Invoices are attributed by last edit, not creation.** They're matched on `updated_by_id` and `modified_date`. If someone else edits an invoice later, or it's edited on another day, it moves to that user/date.
- **Payments are attributed by creator and payment date** (`created_by_id`, `payment_datetime`). Only `status = 'active'` and `outcome = 'complete'` payments are counted.
- Invoices in any status except `cancelled` / `entered_in_error` are counted, **including drafts**.
- `difference` doesn't subtract refunds or credit notes. They're shown separately for manual reconciliation.
- `staff_external_id` is mandatory (not wrapped in `[[ ]]`), so the question won't run without it. If `date` is left empty, the report covers all dates.
- All date filters use IST (`Asia/Kolkata`).

*Last updated: 2026-11-23*
