# Lab Tests with Activity Definition, Reference Ranges and Observation Definition - SSMM

> Laboratory service requests mapped to charge items, specimen, activity and observation definitions with qualified reference ranges

## Purpose

Lists each distinct laboratory test (service request) together with its linked charge item, specimen definition, activity definition, and observation definition, including the observation definition's qualified reference ranges.

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
    emr_chargeitem.title AS charge_item_title,
    emr_specimendefinition.title AS specimen_definition_title,
    emr_activitydefinition.title AS activity_definition_title,
    emr_observationdefinition.title AS observation_definition_title,
    emr_observationdefinition.qualified_ranges AS qualified_ranges
FROM emr_servicerequest
JOIN emr_chargeitem
    ON emr_chargeitem.service_resource_id = emr_servicerequest.external_id::text
LEFT JOIN emr_activitydefinition
    ON emr_activitydefinition.id = emr_servicerequest.activity_definition_id
LEFT JOIN emr_specimen
    ON emr_specimen.service_request_id = emr_servicerequest.id
LEFT JOIN emr_specimendefinition
    ON emr_specimendefinition.id = emr_specimen.specimen_definition_id
LEFT JOIN emr_diagnosticreport
    ON emr_diagnosticreport.service_request_id = emr_servicerequest.id
LEFT JOIN emr_observation
    ON emr_observation.diagnostic_report_id = emr_diagnosticreport.id
LEFT JOIN emr_observationdefinition
    ON emr_observationdefinition.id = emr_observation.observation_definition_id
WHERE emr_servicerequest.status != 'entered_in_error'
  AND emr_chargeitem.status != 'entered_in_error'
  AND emr_servicerequest.category = 'laboratory'
  AND emr_observationdefinition.status = 'active'
ORDER BY emr_servicerequest.category, emr_servicerequest.title;
```

## Notes

- **Lab-only filter:** `emr_servicerequest.category = 'laboratory'` limits the output to laboratory requests.
- **Error-state exclusion:** Both service requests and charge items with `status = 'entered_in_error'` are excluded.
- Results are sorted by service category and service title.

*Last updated: 2026-09-30*
