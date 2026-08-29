# ASAP - Today Booked in - Arike

> Count of urgent ASAP - Today appointments currently booked

## Purpose

This query provides a count of active ASAP - Today appointments that are currently booked. It's useful for monitoring urgent care demand and ensuring timely response to critical patient needs in the Arike program.

## Parameters

*This query has no parameters.*

---

## Query

```sql
SELECT COUNT(*) AS appointment_count
FROM emr_tokenbooking tb
JOIN emr_tokenslot ts 
  ON tb.token_slot_id = ts.id
JOIN emr_schedulableresource sr 
  ON ts.resource_id = sr.id
JOIN emr_tagconfig et 
  ON et.id = ANY(tb.tags)
WHERE tb.status = 'booked'
  AND sr.facility_id = 2
  AND et.display = 'ASAP - Today'
  AND tb.deleted = FALSE  
  AND ts.deleted = FALSE
  AND sr.deleted = FALSE;
```


## Notes

- Query is filtered to `facility_id = 2` - update this value as needed
- Only counts appointments tagged with 'ASAP - Today' - verify this tag display value matches your setup
- Only includes bookings with status = 'booked'
- Uses ANY operator to check if 'ASAP - Today' tag exists in the tags array
- All deleted records are excluded from the count

*Last updated: 2026-01-09*
