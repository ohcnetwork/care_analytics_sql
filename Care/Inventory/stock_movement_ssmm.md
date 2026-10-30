# Stock Movement - SSMM

> Line-level history of every supply delivery, with batch, origin, destination, value, and patient

## Purpose

Lists every stock movement recorded as a supply delivery, covering supplier purchases, internal transfers between locations, and patient returns. Each row shows the product batch, quantity, purchase value, where the stock moved from and to, and who created it. Useful for tracing the movement history of a product or batch.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `product` | text | Optional. Exact product name (`emr_productknowledge.name`) | `Paracetamol 500mg` |
| `date` | field filter | Optional. Date filter mapped to `emr_supplydelivery.created_date` | `Last 30 days` |
| `status` | field filter | Optional. Status filter mapped to `emr_supplydelivery.status` | `completed` |

---

## Query

```sql
SELECT
    ep.batch ->> 'lot_number' AS batch,
    esd.created_date AS moved_at,
    pk.name AS item,
    o.name AS supplier,
    fl_o.name AS origin,
    fl_d.name AS destination,
    esd.supplied_item_quantity AS qty,
    esd.status,
    ep.purchase_price,
    esd.supplied_item_quantity * ep.purchase_price AS value,
    u.first_name AS created_by,
    edo.id AS order_id,
    esd.id AS delivery_id,
    ep.id AS product_id,
    p.name AS patient
FROM emr_supplydelivery esd
JOIN emr_deliveryorder edo ON edo.id = esd.order_id
LEFT JOIN emr_inventoryitem eii ON eii.id = esd.supplied_inventory_item_id
JOIN emr_product ep ON ep.id = COALESCE(eii.product_id, esd.supplied_item_id)
JOIN emr_productknowledge pk ON pk.id = ep.product_knowledge_id
LEFT JOIN emr_facilitylocation fl_o ON fl_o.id = edo.origin_id
LEFT JOIN emr_facilitylocation fl_d ON fl_d.id = edo.destination_id
LEFT JOIN emr_organization o ON o.id = edo.supplier_id
LEFT JOIN users_user u ON u.id = esd.created_by_id
LEFT JOIN emr_patient p ON p.id = edo.patient_id
WHERE esd.deleted = FALSE
  AND edo.deleted = FALSE
--   [[AND pk.name = {{product}}]]
--   [[AND {{date}}]]
--   [[AND {{status}}]]
ORDER BY ep.id, esd.created_date;
```

## Notes

- **Movement type by column:**
  - Supplier purchase: `supplier` is set and `origin` is empty.
  - Internal transfer: both `origin` and `destination` are set.
  - Patient return: `patient` is set.
- **Value:** `supplied_item_quantity × purchase_price`, i.e. the movement valued at purchase cost.
- **Batch:** Read from the `lot_number` key of the product's `batch` JSON.
 - **Field filters:** When enabling the optional Metabase filters, map `{{date}}` to `emr_supplydelivery.created_date` and set its **Table and field alias** to `esd.created_date`; map `{{status}}` to `emr_supplydelivery.status` and set its **Table and field alias** to `esd.status`.
- **Product filter:** `{{product}}` is an exact, case-sensitive match on the product name.
- **Ordering:** Sorted by `product_id` and then `moved_at`, so each product batch reads as a timeline.

*Last updated: 2026-10-29*
