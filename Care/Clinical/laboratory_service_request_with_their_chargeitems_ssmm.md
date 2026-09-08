# Laboratory Service Requests with Their Charge Items - SSMM

> Distinct laboratory service requests mapped to their linked charge items

## Purpose

Lists each laboratory service request together with the charge item linked through the service request external id.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| *(none)* | - | Query runs as a static report with fixed filters | - |

---

## Query

```sql
SELECT DISTINCT
		emr_servicerequest.title AS service_title,
		emr_servicerequest.category AS service_category,
		emr_chargeitem.title AS charge_item_title
FROM emr_servicerequest
JOIN emr_chargeitem
		ON emr_chargeitem.service_resource = 'service_request'
	 AND emr_chargeitem.service_resource_id = emr_servicerequest.external_id::text
WHERE emr_servicerequest.status != 'entered_in_error'
  AND emr_chargeitem.status != 'entered_in_error'
	AND emr_servicerequest.category = 'laboratory'
ORDER BY emr_servicerequest.category, emr_servicerequest.title;
```

## Notes

- **Lab-only filter:** `emr_servicerequest.category = 'laboratory'` limits the output to laboratory requests.
- Results are sorted by service category and service title.

*Last updated: 2026-08-31*
