
# Purchase Report - Pallium

> Detailed line-level purchase / supply delivery report with supplier, destination, batch, expiry and purchase value

## Purpose

Line-by-line view of stock received via supply deliveries at Pallium. Each row represents one supply delivery and shows the supplier, destination location, product, batch / expiry details, unit purchase price, quantity delivered and the total purchase value.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE / range | Metabase date filter (typically bound to `sd.created_date`) | `'2026-05-01'` |
| `supplier_name` | TEXT | Filter by supplier organisation name (exact match) | `'ABC Pharma'` |
| `stock_name` | TEXT | Filter by product / stock name (exact match) | `'Paracetamol'` |

---

## Query

```sql
SELECT
  sd.created_date AS supply_date,
  org.name AS supplier_name,
  fl.name AS destination,
  p.batch->>'lot_number' AS lot_number,
  p.expiration_date,
  pk.name AS product_name,
  p.purchase_price,
  sd.supplied_item_quantity * p.purchase_price AS total_purchase,
  sd.supplied_item_quantity AS quantity_delivered
FROM emr_supplydelivery sd
JOIN emr_inventoryitem ii ON sd.supplied_inventory_item_id = ii.id
JOIN emr_product p ON ii.product_id = p.id
JOIN emr_productknowledge pk ON p.product_knowledge_id = pk.id
JOIN emr_deliveryorder d ON sd.order_id = d.id
JOIN emr_organization org ON d.supplier_id = org.id
JOIN emr_facilitylocation fl ON d.destination_id = fl.id
WHERE sd.status NOT IN ('entered_in_error', 'abandoned')
  --[[AND {{date}}]]
  --[[AND org.name = {{supplier_name}}]]
  --[[AND pk.name = {{stock_name}}]]
ORDER BY supplier_name;
```

## Notes

- **Metabase filters:**
  - `[[AND {{date}}]]` is a field filter — bind it to `sd.created_date` (or whatever date column you want filterable) in the Metabase variable settings.
  - `[[AND org.name = {{supplier_name}}]]` and `[[AND pk.name = {{stock_name}}]]` are exact-match text filters on supplier and product name.

*Last updated: 2026-05-25*

````

