
# Expiring Items - Next Month

> Inventory items expiring in the next calendar month, with batch, supplier, and supply details

## Purpose

Lists active inventory products at a specific facility whose `expiration_date` falls within the next calendar month. Each row shows the batch / lot number, stock name, quantity supplied, supply date, expiry date, and the originating supplier.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `stock_name` | TEXT | Filter by stock / product name (exact match on `emr_productknowledge.name`) | `'Paracetamol'` |
| `supplier` | TEXT | Filter by supplier organization name (exact match on `emr_organization.name`) | `'MedSupplier Pvt Ltd'` |

---

## Query

```sql
SELECT
    p.batch ->> 'lot_number' AS batch,
    pk.name AS stock_name,
    sd.supplied_item_quantity AS quantity,
    sd.created_date AS supply_date,
    p.expiration_date AS expiry_date,
    org.name AS supplier_name
FROM emr_inventoryitem ii
JOIN emr_product p ON ii.product_id = p.id
JOIN emr_productknowledge pk ON p.product_knowledge_id = pk.id
JOIN emr_supplydelivery sd ON sd.supplied_inventory_item_id = ii.id
JOIN emr_deliveryorder d ON sd.order_id = d.id
JOIN emr_organization org ON d.supplier_id = org.id
WHERE p.status = 'active'
  AND p.facility_id = 11
  AND sd.status IN ('completed','in_progress')
  AND p.expiration_date >= date_trunc('month', CURRENT_DATE + INTERVAL '1 month')
  AND p.expiration_date <  date_trunc('month', CURRENT_DATE + INTERVAL '2 months')
  --[[AND pk.name = {{stock_name}}]]
  --[[AND org.name = {{supplier}}]]
ORDER BY p.expiration_date, pk.name, batch;
```

## Notes

- The date window covers **the next calendar month** (from the 1st of next month up to but not including the 1st of the month after). Adjust the `INTERVAL` values to widen or shift the window.
- `p.facility_id = 11` is hardcoded — change this to target a different facility.
- Only products with `status = 'active'` and supply deliveries in `completed` / `in_progress` status are included.
- Batch number is extracted from the `p.batch` JSONB column via `->> 'lot_number'`.
- Results are ordered by earliest expiry first, then stock name and batch.

*Last updated: 2026-06-17*
