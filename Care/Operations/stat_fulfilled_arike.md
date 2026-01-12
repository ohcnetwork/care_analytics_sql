# STAT Fulfilled - Arike

> Count of urgent STAT appointments that have been fulfilled

## Purpose

This query provides a count of STAT (urgent "Right Now") appointments that have been fulfilled. It's useful for monitoring urgent care completion rates and tracking response to critical patient needs in the Arike program.

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
WHERE tb.status = 'fulfilled'
  AND sr.facility_id = 2
  AND et.display = 'STAT - Right Now'
  AND tb.deleted = FALSE  
  AND ts.deleted = FALSE
  AND sr.deleted = FALSE;
```


## Notes

- Query is filtered to `facility_id = 2` - update this value as needed
- Only counts appointments tagged with 'STAT - Right Now' - verify this tag display value matches your setup
- Only includes bookings with status = 'fulfilled'
- Uses ANY operator to check if 'STAT - Right Now' tag exists in the tags array
- All deleted records are excluded from the count

*Last updated: 2026-01-09*
