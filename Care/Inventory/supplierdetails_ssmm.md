# Supplier Delivery Details

> Track supply deliveries with supplier and product information

## Purpose

This query provides a detailed view of supply deliveries, showing which suppliers delivered which products and in what quantities. It's useful for inventory tracking, supplier performance monitoring, and delivery verification.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | DATE | Filters deliveries by creation date | `DATE(sd.created_date) = '2025-12-20'` |

---

## Query

```sql
SELECT
  DATE(sd.created_date) AS supply_date,
  org.name AS supplier_name,
  p.batch->>'lot_number' AS lot_number,
  p.expiration_date,
  pk.name AS product_name,
  sd.supplied_item_quantity AS quantity_delivered
FROM emr_supplydelivery sd
LEFT JOIN emr_inventoryitem ii ON sd.supplied_inventory_item_id = ii.id
LEFT JOIN emr_product p ON ii.product_id = p.id
LEFT JOIN emr_productknowledge pk ON p.product_knowledge_id = pk.id
LEFT JOIN emr_deliveryorder d ON sd.order_id = d.id 
LEFT JOIN emr_organization org ON d.supplier_id = org.id
-- WHERE 1=1
--   [[AND {{date}}]]
ORDER BY sd.created_date DESC;
```


## Notes

- Results are ordered by most recent delivery first
- The `lot_number` is extracted from the batch JSONB field
- The optional `date` parameter allows filtering by specific delivery dates

*Last updated: 2025-12-20*
