
# Patient Medication Return

> Line-level list of medication returns from patients with batch, destination, invoice, and staff details

## Purpose

Lists completed medication returns at Pallium where stock has been delivered **back from a patient** into a facility location. Each row shows the medication, patient (with MRN), quantity returned, destination location, originating invoice, return date, and the user who recorded the return.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE / range | Metabase date filter (typically bound to `sd.created_date`) | `'2026-06-01'` |

---

## Query

```sql
SELECT
    pk.name AS medication_name,
    p_patient.name AS patient_name,
    pi.value AS mrn,
    sd.supplied_item_quantity AS quantity_returned,
    fl.name AS returned_to_destination,
    inv.number AS invoice_number,
    sd.created_date AS return_date,
    TRIM(created_user.first_name || ' ' || created_user.last_name, '') AS created_by
FROM emr_supplydelivery sd
JOIN emr_deliveryorder dorder
    ON sd.order_id = dorder.id
JOIN emr_patient p_patient
    ON dorder.patient_id = p_patient.id
LEFT JOIN emr_patientidentifier pi
    ON p_patient.id = pi.patient_id
   AND pi.config_id = 4
JOIN emr_invoice inv
    ON dorder.patient_invoice_id = inv.id
JOIN emr_facilitylocation fl
    ON dorder.destination_id = fl.id
JOIN emr_inventoryitem ii
    ON sd.supplied_inventory_item_id = ii.id
JOIN emr_product p
    ON ii.product_id = p.id
JOIN emr_productknowledge pk
    ON p.product_knowledge_id = pk.id
LEFT JOIN users_user created_user
    ON sd.created_by_id = created_user.id
WHERE dorder.patient_id IS NOT NULL
  AND dorder.supplier_id IS NULL
  AND sd.status = 'completed'
  --[[AND {{date}}]]
ORDER BY sd.created_date DESC;
```

## Notes

- **Return semantics:** A delivery is treated as a *patient return* when the `emr_deliveryorder` has a `patient_id` set **and** no `supplier_id` — i.e. the stock is flowing back from the patient into a facility location rather than from a supplier.
- **Destination:** `dorder.destination_id` joined to `emr_facilitylocation` shows the inventory location the medication was returned to.
- **Metabase filter:** `[[AND {{date}}]]` is a field filter — bind it to `sd.created_date` in the Metabase variable settings.
- Results are ordered by most recent `return_date` first.

*Last updated: 2026-06-29*
