# Casualty Appointments Booked

> Track the count of booked appointments for Casualty service

## Purpose

Monitor and analyze the number of booked appointments for the Casualty healthcare service. Helps track appointment demand and scheduling patterns for emergency care services.

## Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `booking_date` | DATE | Filter by appointment booking date range (optional) | `2025-12-01 TO 2025-12-31` |

---

## Query

```sql
SELECT
    COUNT(public.emr_tokenbooking.id) AS booked_appointments
FROM public.emr_tokenbooking
JOIN public.emr_tokenslot ON public.emr_tokenbooking.token_slot_id = public.emr_tokenslot.id
JOIN public.emr_schedulableresource ON public.emr_tokenslot.resource_id = public.emr_schedulableresource.id
JOIN public.emr_healthcareservice ON public.emr_schedulableresource.healthcare_service_id = public.emr_healthcareservice.id
WHERE public.emr_tokenbooking.status = 'booked'
  AND public.emr_healthcareservice.name = 'Casualty'
  --   [[AND {{booking_date}}]]
;
```

### Output

| Column | Type | Description |
|--------|------|-------------|
| `booked_appointments` | INTEGER | Total count of booked appointments for Casualty service |

---

## Notes

- Metabase-specific filters (`[[...]]`) allow dynamic filtering in dashboards.
- The query counts booked appointments from the emr_tokenbooking table.
- Only appointments with status `'booked'` are included.
- Only appointments for the `'Casualty'` healthcare service are included.
- Ensure all referenced tables and fields exist and are mapped correctly.
- All filters are optional and applied dynamically by Metabase.

*Last updated: 2025-12-16*
