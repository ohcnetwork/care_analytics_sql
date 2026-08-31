# Care Database Skill

> AI reference for generating accurate SQL queries on Care HMIS database.

---

## ⚠️ CRITICAL RULES FOR AI

1. **ALWAYS verify table columns** before writing queries using `information_schema`
2. **ALWAYS use `deleted = false`** - All tables have soft delete
3. **"Patient ID" ALWAYS means `emr_patientidentifier.value`** — NOT the internal `emr_patient.id`. ALWAYS filter by a specific `config_id` (ask the user which one, or run the discovery query). Joining without `config_id` returns multiple rows per patient. Internal `p.id` is for joins only, never for display.
4. **Patient identifier `config_id` is instance-specific** - Must be looked up per deployment
5. **Parent tag IDs are instance-specific** - Discover them first before querying
6. **For reports use SQL queries** - Simple counts can use Metabase query builder
7. **Cross-check with source docs** if schema changes: https://docs.ohc.network
8. **Exclude `entered_in_error` rows** — records created by mistake keep `deleted = false` but are invalidated by `status`; on every table with a `status` column also exclude terminal statuses the report requires (`cancelled` invoices in revenue, etc.)
9. **Keep queries lean — tables hold thousands of rows** — minimise joins/subqueries, keep predicates sargable (no `DATE()`/`LOWER()` on filtered columns; use range comparisons), never aggregate after a one-to-many join (pre-aggregate in a CTE), and remember JSONB/array access has no index

```sql
-- Verify table columns before writing ANY query
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = '<table_name>' ORDER BY ordinal_position;

-- Check distinct values for status/enum fields
SELECT DISTINCT <column> FROM <table> WHERE deleted = false;
```

---

## 🔍 WHEN WRITING QUERIES, ASK USER FOR:

| If query involves... | Ask user for... | Why? |
|---------------------|-----------------|------|
| Patient identifier | `config_id` value | Different per instance (e.g., 21 for SSMM ID, 4 for pallium ID) |
| Tag filtering (zone, area) | `parent_id` of the tag | Tags are instance-specific |
| Facility-specific data | `facility_id` | To filter to correct facility |
| Questionnaire responses | Questionnaire ID and question UUID | Forms vary per deployment |
| Date filtering | Which date field to use | Options: `created_date`, `recorded_date`, `date_joined`, etc. |
| Department/team filtering | Department name pattern | e.g., '%jak%' for JAK department |
| Geographic filtering | District/Local body name or level | Filter by `metadata->>'govt_org_type'`; `level_cache` only safe for state (0) / district (1) unless discovered |

**Always provide helper queries** so user can find these values themselves. If the user doesn't know a value, give them the relevant query below so they can look it up.

**⚠️ When guiding a user through discovery, give queries ONE AT A TIME** — each step depends on the previous result (questionnaire list → user confirms ID → question list for that ID → user confirms UUID → answer values). Fill confirmed values into the next query yourself; never hand the user a query with unfilled placeholders.

### Discovery Queries for Instance-Specific Values

**Find patient identifier config_id:**
```sql
SELECT id, config->>'display' AS identifier_name, status
FROM emr_patientidentifierconfig
WHERE deleted = false AND status = 'active'
ORDER BY id;
```

**Find facility_id:**
```sql
SELECT id, name, is_active
FROM facility_facility
WHERE deleted = false AND is_active = true
ORDER BY name;
```

**Find tag parent_id (zones, areas, teams):**
```sql
-- Top-level tags (parents)
SELECT id, display, category
FROM emr_tagconfig
WHERE deleted = false AND parent_id IS NULL
ORDER BY category, display;

-- Children of a specific parent — run after getting parent id from above
SELECT id, display, parent_id
FROM emr_tagconfig
WHERE deleted = false
ORDER BY parent_id, display;
```

**Find questionnaire IDs (⚠️ list ALL — never filter by title keywords; titles vary per deployment):**
```sql
SELECT q.id, q.title, q.slug, q.subject_type, COUNT(qr.id) AS response_count
FROM emr_questionnaire q
LEFT JOIN emr_questionnaireresponse qr ON q.id = qr.questionnaire_id AND qr.deleted = false
WHERE q.deleted = false AND q.status = 'active'
GROUP BY q.id, q.title, q.slug, q.subject_type
ORDER BY response_count DESC;
```

**Find question UUIDs (⚠️ recursive — forms nest groups inside groups, 3+ levels deep; a flat 2-level query MISSES questions). Lists every question with its number, readable path and answer options — the user picks by number/name, never by UUID:**
```sql
WITH RECURSIVE question_tree AS (
    SELECT emr_questionnaire.id AS questionnaire_id,
           question AS node,
           question->>'text' AS path
    FROM emr_questionnaire,
    LATERAL jsonb_array_elements(emr_questionnaire.questions) AS question
    WHERE emr_questionnaire.id IN (<questionnaire_ids>)
      AND emr_questionnaire.deleted = false
    UNION ALL
    SELECT question_tree.questionnaire_id,
           child AS node,
           question_tree.path || ' > ' || (child->>'text') AS path
    FROM question_tree,
    LATERAL jsonb_array_elements(question_tree.node->'questions') AS child
    WHERE jsonb_typeof(question_tree.node->'questions') = 'array'
)
SELECT question_tree.questionnaire_id,
       question_tree.node->>'link_id' AS q_no,
       question_tree.path AS question,
       question_tree.node->>'type' AS answer_type,
       (SELECT string_agg(opt->>'value', ' | ')
        FROM jsonb_array_elements(question_tree.node->'answer_option') AS opt) AS answer_options,
       question_tree.node->>'id' AS question_uuid
FROM question_tree
WHERE question_tree.node->>'type' != 'group'   -- hide section headers, show real questions only
ORDER BY question_tree.questionnaire_id, question_tree.path;
```
- `answer_options` shows the exact allowed spellings for `choice` questions — often no need for a separate answer-values check.
- `answer_options` is EMPTY for value-set questions (`answer_value_set`, e.g. arike-nc-list) — for those, check actually-recorded values from responses.

**Find department/team names:**
```sql
SELECT id, name, org_type
FROM emr_facilityorganization
WHERE deleted = false
ORDER BY org_type, name;
```

**Find district IDs:**
```sql
SELECT id, name
FROM emr_organization
WHERE deleted = false AND org_type = 'govt' AND level_cache = 1
ORDER BY name;
```

---

## Database: `care.ohc.network` (ID: 3)

---

## TABLE SCHEMAS

### emr_patient
```
id                    bigint
external_id           uuid
name                  varchar
gender                varchar (male, female, other, unknown)
date_of_birth         date
age                   integer
phone_number          varchar
address               text
pincode               integer
blood_group           varchar
instance_tags         ARRAY (array of tag IDs)
geo_organization_id   bigint → emr_organization
created_date          timestamptz
deleted               boolean
```

### emr_patientidentifier
```
id                    bigint
external_id           uuid
value                 varchar (the actual identifier value)
config_id             bigint → emr_patientidentifierconfig
patient_id            bigint → emr_patient
facility_id           bigint → facility_facility
created_date          timestamptz
deleted               boolean
```

### emr_patientidentifierconfig
```
id                    bigint
external_id           uuid
config                jsonb (contains: display, system, use, regex, unique, required)
status                varchar (active, inactive, draft)
facility_id           bigint
deleted               boolean
```
**Access display name:** `config->>'display'`

### emr_condition (Diagnoses)
```
id                    bigint
external_id           uuid
code                  jsonb (diagnosis code)
clinical_status       varchar
verification_status   varchar
category              varchar
severity              varchar
body_site             jsonb
onset                 jsonb
abatement             jsonb
recorded_date         timestamptz
note                  text
patient_id            bigint → emr_patient
encounter_id          bigint → emr_encounter
created_date          timestamptz
deleted               boolean
```

### emr_encounter
```
id                    bigint
external_id           uuid
status                varchar (planned, in-progress, completed, cancelled)
encounter_class       varchar (imp, amb, emer, hh, obsenc)
priority              varchar
period_start          timestamptz
period_end            timestamptz
patient_id            bigint → emr_patient
facility_id           bigint → facility_facility
created_date          timestamptz
deleted               boolean
```

### emr_tokenbooking (Appointments)
```
id                    bigint
external_id           uuid
status                varchar (see lifecycle below)
booked_on             date
note                  text
patient_id            bigint → emr_patient
token_slot_id         bigint → emr_tokenslot
booked_by_id          bigint → users_user
created_date          timestamptz
deleted               boolean
```

**Booking status lifecycle** ([docs](https://docs.ohc.network/concepts/scheduling/booking)):
```
proposed → pending → booked → arrived → checked_in → in_consultation → fulfilled
                       ├──→ cancelled / entered_in_error / rescheduled
                       └──→ noshow
```
| Status | Meaning |
|---|---|
| `booked` | Default on creation — slot reserved |
| `arrived` / `checked_in` | Patient reached the facility |
| `in_consultation` | Patient is being seen |
| `fulfilled` |  use this for "appointments completed/fulfilled" reports |
| `noshow` | Terminal — patient did not turn up |
| `cancelled` / `rescheduled` | Called off / moved. Rescheduling CLOSES the original booking (status=`rescheduled`) and creates a NEW booking on the new slot — so reschedule counts = count of `rescheduled` rows |
| `entered_in_error` | Logged by mistake — exclude from ALL reports |

**Interpreting appointment requests (defaults):**
- "appointments booked / made / number of appointments" = ALL bookings created → `status != 'entered_in_error'` (NOT `status = 'booked'`)
- "completed / patients seen" → `status = 'fulfilled'` · "upcoming/active" → `status = 'booked'`
- Date default: `booked_on` (appointment date); `created_date` only for "when was it booked"
- ⚠️ `emr_tokenbooking` has NO `facility_id` — scope by facility via `emr_tokenslot → emr_schedulableresource.facility_id`

### emr_tagconfig
```
id                    bigint
external_id           uuid
display               varchar (tag name)
description           text
category              varchar
parent_id             bigint → emr_tagconfig (parent tag)
root_tag_config_id    bigint
level_cache           integer
has_children          boolean
resource              varchar
facility_id           bigint
deleted               boolean
```

### emr_organization
```
id                    bigint
external_id           uuid
name                  varchar
org_type              varchar (govt, role, team, product_supplier)
level_cache           integer
parent_id             bigint → emr_organization
root_org_id           bigint
parent_cache          ARRAY
has_children          boolean
metadata              jsonb (govt_org_type: state, district, municipality, etc.)
active                boolean
deleted               boolean
```

#### Government Hierarchy (org_type = 'govt') — ⚠️ VARIES PER DEPLOYMENT

The depth and meaning of `level_cache` differ between deployments. **ONLY levels 0 (state) and 1 (district) are stable everywhere — everything below district varies, so level numbers are deliberately NOT shown below.** Two known shapes:

**Full nesting (some deployments):**
```
State (level 0)
    └── District (level 1)
            └── Local Bodies (district_panchayat, municipality, corporation, other_local_body)
                    └── block_panchayat / ward (under municipality/corporation)
                            └── grama_panchayat
                                    └── ward
```

**Flat shape (other deployments):**
```
State (level 0)
    └── District (level 1)
            └── Local Body (grama_panchayat, block_panchayat, district_panchayat, municipality, corporation)
                    └── ward
```

**NEVER assume levels below district — discover the actual shape of the deployment first:**
```sql
SELECT level_cache, metadata->>'govt_org_type' AS govt_org_type, COUNT(*) AS cnt
FROM emr_organization
WHERE deleted = false AND org_type = 'govt'
GROUP BY level_cache, metadata->>'govt_org_type'
ORDER BY level_cache, govt_org_type;
```

**govt_org_type values** (in `metadata->>'govt_org_type'`): `state`, `district`, `district_panchayat`, `municipality`, `corporation`, `other_local_body`, `block_panchayat`, `grama_panchayat`, `ward`.

⚡ When filtering by org type (e.g. all grama panchayats), prefer `metadata->>'govt_org_type' = 'grama_panchayat'` (stable meaning) over a hardcoded `level_cache` (deployment-dependent). `level_cache = 1` for district is safe everywhere.

### users_user
```
id                    bigint
external_id           uuid
username              varchar
first_name            varchar
last_name             varchar
email                 varchar
phone_number          varchar
user_type             varchar (doctor, nurse, staff, volunteer)
gender                varchar
date_of_birth         date
date_joined           timestamptz
last_login            timestamptz
is_active             boolean
home_facility_id      bigint → facility_facility
geo_organization_id   bigint → emr_organization
deleted               boolean
```

### emr_patientuser (Patient ↔ User Link)
```
id                    bigint
external_id           uuid
created_date          timestamptz
modified_date         timestamptz
patient_id            bigint → emr_patient
user_id               bigint → users_user
role_id               bigint → security_rolemodel
deleted               boolean
```
- Use this table to list patients linked to volunteers/caregivers/staff users.
- Filter volunteers with `users_user.user_type = 'volunteer'` and `deleted = false` on all joined tables.

### security_rolemodel
```
id                    bigint
name                  varchar
is_system             boolean
is_archived           boolean
deleted               boolean
```
- Join from `emr_patientuser.role_id` when you need the role label assigned on the link row.

### facility_facility
```
id                    bigint
external_id           uuid
name                  varchar
facility_type         integer
is_active             boolean
verified              boolean
address               text
pincode               integer
phone_number          varchar
latitude              numeric
longitude             numeric
geo_organization_id   bigint → emr_organization
created_date          timestamptz
deleted               boolean
```

### emr_facilitylocation (Beds, Rooms, Wards)
```
id                    bigint
external_id           uuid
name                  varchar
status                varchar (active, inactive)
operational_status    varchar
form                  varchar (bd=bed, rm=room, wa=ward)
mode                  varchar
level_cache           integer
parent_id             bigint → emr_facilitylocation
root_location_id      bigint → emr_facilitylocation
facility_id           bigint → facility_facility
current_encounter_id  bigint → emr_encounter
deleted               boolean
```

### emr_facilitylocationencounter (Bed Assignments)
```
id                    bigint
external_id           uuid
start_datetime        timestamptz
end_datetime          timestamptz
status                varchar
encounter_id          bigint → emr_encounter
location_id           bigint → emr_facilitylocation
created_by_id         bigint → users_user
created_date          timestamptz
deleted               boolean
```

### emr_invoice
```
id                    bigint
external_id           uuid
number                varchar (invoice number)
title                 varchar
status                varchar (draft, issued, balanced, cancelled)
total_net             numeric
total_gross           numeric
issue_date            timestamptz
cancelled_reason      text
note                  text
patient_id            bigint → emr_patient
account_id            bigint → emr_account
facility_id           bigint → facility_facility
created_by_id         bigint → users_user
updated_by_id         bigint → users_user
created_date          timestamptz
modified_date         timestamptz
deleted               boolean
```

### emr_questionnaire
```
id                    bigint
external_id           uuid
title                 varchar
slug                  varchar
status                varchar (active, draft, retired)
subject_type          varchar (patient, encounter)
questions             jsonb (array of question objects)
deleted               boolean
```

### emr_questionnaireresponse
```
id                    bigint
external_id           uuid
questionnaire_id      bigint → emr_questionnaire
patient_id            bigint → emr_patient
encounter_id          bigint → emr_encounter
responses             jsonb (array of {question_id, values})
created_date          timestamptz
deleted               boolean
```

### emr_account (Patient Billing Account)
```
id                    bigint
external_id           uuid
status                varchar
billing_status        varchar
name                  varchar
tags                  ARRAY (array of tag IDs)
patient_id            bigint → emr_patient
facility_id           bigint → facility_facility
primary_encounter_id  bigint → emr_encounter
total_net             numeric
total_gross           numeric
total_paid            numeric  ← total amount paid directly on the account
total_balance         numeric  ← outstanding due amount (positive = owes money)
total_billable_charge_items numeric
calculated_at         timestamptz
created_date          timestamptz
modified_date         timestamptz
created_by_id         bigint → users_user
updated_by_id         bigint → users_user
deleted               boolean
```
- Use `total_balance > 0` to filter patients with a due amount.
- `total_paid` and `total_balance` are pre-computed — no need to join `emr_paymentreconciliation` for these totals.

### emr_servicerequest (Orders: lab, imaging, procedures)
```
id                    bigint
external_id           uuid
title                 varchar
category              varchar (laboratory, imaging, surgical_procedure, counselling)
status                varchar (active, completed, on_hold, revoked, entered_in_error)
intent                varchar
priority              varchar
code                  jsonb (what was ordered)
occurance             timestamptz
locations             ARRAY
tags                  ARRAY
patient_id            bigint → emr_patient
encounter_id          bigint → emr_encounter
facility_id           bigint → facility_facility
healthcare_service_id bigint → emr_healthcareservice
requester_id          bigint → users_user
created_date          timestamptz
deleted               boolean
```
- "Number of scans / x-rays / lab tests ordered" = count service requests with the right `category`. Exclude `entered_in_error` and `revoked`.

### emr_diagnosticreport (Lab/imaging results)
```
id, external_id, status (registered, preliminary, final), category jsonb, code jsonb,
conclusion text, note text, patient_id, encounter_id, facility_id,
service_request_id → emr_servicerequest, created_date, deleted
```
- One report fulfils one service request. "Completed lab tests" → `status = 'final'`.

### emr_specimen (Lab samples)
```
id, external_id, accession_identifier varchar, status (available, draft, unsatisfactory, unavailable, entered_in_error),
specimen_type jsonb, received_time timestamptz, collection jsonb, processing jsonb,
patient_id, encounter_id, facility_id, service_request_id → emr_servicerequest, created_date, deleted
```

### emr_observation (Vitals, lab values, structured findings)
```
id, external_id, status (final, entered_in_error), is_group boolean, category jsonb,
main_code jsonb (LOINC code), value_type varchar, value jsonb, component jsonb,
effective_datetime timestamptz, note text, body_site jsonb, reference_range jsonb, interpretation jsonb,
patient_id, encounter_id, questionnaire_response_id → emr_questionnaireresponse,
diagnostic_report_id → emr_diagnosticreport, created_date, deleted
```
- Vitals entered via questionnaires ALSO land here as coded observations (`main_code` = LOINC, e.g. 8480-6 systolic BP) linked via `questionnaire_response_id` — often easier to query than the responses JSONB.
- Use `status = 'final'`; access the value with `value->>'value'` or per `value_type`.

### emr_medicationrequest (Prescriptions)
```
id, external_id, status (active, ended, entered_in_error), status_reason varchar, intent varchar,
category varchar, priority varchar, do_not_perform boolean, medication jsonb,
dosage_instruction jsonb, authored_on timestamptz, dispense_status varchar,
patient_id, encounter_id, requester_id → users_user, prescription_id, created_date, deleted
```

### emr_medicationstatement (What patient reports taking)
```
id, external_id, status, reason varchar, medication jsonb, effective_period jsonb,
information_source varchar, dosage_text text, patient_id, encounter_id, created_date, deleted
```

### emr_allergyintolerance
```
id, external_id, clinical_status, verification_status, category, criticality,
code jsonb, onset jsonb, recorded_date, last_occurrence, note,
patient_id, encounter_id, created_date, deleted
```

### emr_chargeitem (Billing line items — what was charged)
```
id, external_id, title varchar, status (billable, billed, paid, aborted, not_billable, entered_in_error),
code jsonb, quantity numeric, unit_price_components jsonb, total_price numeric,
service_resource varchar, service_resource_id varchar, tags ARRAY,
account_id → emr_account, patient_id, encounter_id, facility_id,
charge_item_definition_id, paid_invoice_id → emr_invoice, paid_on timestamptz, created_date, deleted
```
- Revenue by service/item = SUM(total_price) grouped by code/title. Exclude `aborted`, `not_billable`, `entered_in_error`.

### emr_paymentreconciliation (Payments received)
```
id, external_id, reconciliation_type varchar, status (active, cancelled, entered_in_error),
kind varchar, outcome varchar, method (cash, chck, ccca, debc, ddpo, cdac),
payment_datetime timestamptz, reference_number varchar,
tendered_amount numeric, returned_amount numeric, amount numeric,
account_id → emr_account, target_invoice_id → emr_invoice, facility_id,
is_credit_note boolean, location_id, created_date, deleted
```
- "Payments collected" = SUM(amount) with `status = 'active'` (exclude `cancelled`, `entered_in_error`).
- Payment-mode split: group by `method` (cash, chck=cheque, ccca=credit card, debc=debit card, ...).

### emr_consent
```
id, external_id, status, category varchar, date timestamptz, period jsonb,
decision varchar, verification_details jsonb, encounter_id, created_date, deleted
```
- Note: links via `encounter_id` only (no direct patient_id).

### emr_facilityorganization (Departments/teams inside a facility)
```
id, external_id, name varchar, org_type (root, dept, team), active boolean,
level_cache integer, parent_cache ARRAY, parent_id, root_org_id,
facility_id → facility_facility, deleted
```
- ⚠️ Different from `emr_organization` (geo/govt hierarchy). This one is INTERNAL structure: departments (`dept`) and teams (`team`) under a facility `root`.

### emr_facilityorganizationuser (User ↔ department/team membership)
```
id, external_id, organization_id → emr_facilityorganization, user_id → users_user,
role_id → security_rolemodel, created_date, deleted
```
- "Users in department X" = join this to emr_facilityorganization (name ILIKE) + users_user (`is_active = TRUE`).

### emr_healthcareservice (Bookable services, e.g. physio, counselling)
```
id, external_id, name varchar, service_type jsonb, internal_type varchar,
locations ARRAY, extra_details text, facility_id, managing_organization_id, deleted
```

### emr_tokenslot (Appointment slots)
```
id, external_id, start_datetime timestamptz, end_datetime timestamptz,
allocated integer (bookings taken on this slot), availability_id,
resource_id → emr_schedulableresource, created_date, deleted
```

### 💊 Pharmacy & Inventory chain
Chain: **productknowledge** (what a drug IS) → **product** (a purchased batch) → **inventoryitem** (stock at a location) → **supplyrequest/supplydelivery** (stock movement) → **medicationdispense** (handed to patient).

```
emr_productknowledge   (drug/product catalog)
  id, slug, alternate_identifier, status, product_type, code jsonb, name, names jsonb,
  names_cache varchar, base_unit jsonb, category_id, facility_id, deleted

emr_product            (a batch of a product at a facility)
  id, status, product_type, batch jsonb, expiration_date, purchase_price numeric,
  standard_pack_size int, product_knowledge_id, charge_item_definition_id, facility_id, deleted

emr_inventoryitem      (current stock at a location)
  id, status ('active'; some blank), net_content numeric (qty on hand),
  product_id → emr_product, location_id → emr_facilitylocation, deleted

emr_supplyrequest      (internal stock request)
  id, status (active, completed, processed, cancelled, draft, entered_in_error),
  quantity numeric, item_id, order_id, deleted

emr_supplydelivery     (stock movement/fulfilment)
  id, status (completed, in_progress, abandoned, entered_in_error),
  supplied_item_quantity numeric, supplied_item_pack_quantity int, total_purchase_price numeric,
  supplied_inventory_item_id, supplied_item_id, supply_request_id, order_id, deleted

emr_requestorder       (procurement order to supplier)
  id, name, status (pending, draft, completed, abandoned, entered_in_error),
  category, intent, priority, origin_id, destination_id, supplier_id, deleted

emr_deliveryorder      (goods received)
  id, name, status (completed, draft, pending, abandoned, entered_in_error),
  origin_id, destination_id, supplier_id, patient_id, patient_invoice_id, deleted

emr_dispenseorder      (pharmacy dispense order)
  id, name, alternate_identifier, status (completed, draft, in_progress, abandoned, entered_in_error),
  patient_id, location_id, facility_id, deleted
```

### emr_medicationdispense (Pharmacy handing out drugs)
```
id, status (completed, preparation, in_progress, cancelled, declined, on_hold, stopped, entered_in_error),
category, quantity numeric, days_supply numeric, when_prepared, when_handed_over timestamptz,
dosage_instruction jsonb, substitution jsonb, authorizing_request_id → emr_medicationrequest,
charge_item_id → emr_chargeitem, item_id, order_id → emr_dispenseorder,
patient_id, encounter_id, location_id, created_date, deleted
```
- "Medicines dispensed" → `status = 'completed'`. Pharmacy revenue joins via `charge_item_id`.

### emr_medicationadministration (Drugs actually given, e.g. IV in ward)
```
id, status (completed, in_progress, not_done, on_hold, cancelled, stopped, entered_in_error),
category, medication jsonb, occurrence_period_start/end timestamptz, recorded timestamptz,
dosage jsonb, request_id → emr_medicationrequest, administered_product_id,
patient_id, encounter_id, created_date, deleted
```

### emr_medicationrequestprescription (Prescription grouping)
```
id, name, alternate_identifier, status (active, completed, cancelled), approval_status,
prescribed_by_id → users_user, patient_id, encounter_id, created_date, deleted
```
- `emr_medicationrequest.prescription_id` points here; one prescription groups many drug requests.

### emr_chargeitemdefinition (Price list / rate card)
```
id, version int, status, title, slug, description, purpose,
price_components jsonb (the actual prices/taxes), tags ARRAY, category_id, facility_id, deleted
```

### emr_resourcerequest (Referrals / patient transfers between facilities)
```
id, title, status, emergency boolean, reason text, category, priority int,
origin_facility_id, assigned_facility_id, approving_facility_id,
assigned_to_id → users_user, related_patient_id → emr_patient, created_date, deleted
```
- ⚠️ **status values are MIXED CASE in production** (`pending` AND `PENDING`, `'ON HOLD'` with a space) — always normalize: `LOWER(REPLACE(status, ' ', '_')) = 'pending'`.

### 🎫 Queue tokens (walk-in queue, different from appointment bookings)
```
emr_token       id, number int, status (⚠️ UPPERCASE: CREATED, FULFILLED, IN_PROGRESS, CANCELLED, UNFULFILLED, ENTERED_IN_ERROR),
                is_next boolean, patient_id, facility_id, booking_id → emr_tokenbooking,
                queue_id, sub_queue_id, category_id, deleted
emr_tokenqueue  id, name, is_primary, date date, resource_id → emr_schedulableresource, facility_id, deleted
```

### 📅 Schedule config (supply side of appointments)
```
emr_schedule      id, name, valid_from, valid_to, resource_id → emr_schedulableresource,
                  charge_item_definition_id (visit price), revisit_allowed_days, is_public, deleted
emr_availability  id, name, slot_type, slot_size_in_minutes, tokens_per_slot,
                  availability jsonb (weekly pattern), schedule_id, deleted
```

### 📝 Clinical notes (free-text threads, NOT questionnaires)
```
emr_notethread   id, title, patient_id, encounter_id, created_by_id, created_date, deleted
emr_notemessage  id, message text, thread_id → emr_notethread, created_by_id, created_date, deleted
```

### 📎 Files & reports
```
emr_fileupload   id, name, file_type, file_category, associating_id varchar (external_id of ANY linked
                 resource, e.g. encounter/patient), upload_completed, is_archived, created_date, deleted
emr_reportupload id, name, report_type, associating_id, template_id, is_archived, created_date, deleted
```

### 🔗 Org membership links
```
emr_organizationuser      user ↔ emr_organization (geo/govt/team) membership: organization_id, user_id, role_id, deleted
emr_encounterorganization encounter ↔ emr_facilityorganization: which departments an encounter belongs to (encounter_id, organization_id, deleted)
emr_patientorganization   patient ↔ emr_organization (patient's geo orgs): patient_id, organization_id, deleted
```
- District-wise USER reports → `emr_organizationuser` + `emr_organization`. Department-wise ENCOUNTER reports → `emr_encounterorganization` + `emr_facilityorganization`.

### emr_valueset (Reusable answer lists)
```
id, slug, name, status, compose jsonb (the allowed values), is_system_defined, deleted
```
- Questionnaire questions with `answer_value_set` (e.g. `arike-nc-list`) get their options HERE: `SELECT compose FROM emr_valueset WHERE slug = '<answer_value_set>'` — alternative to checking recorded answers.

### emr_activitydefinition (Orderable service definitions, e.g. specific lab tests)
```
id, slug, title, status, classification, kind, code jsonb, category_id,
charge_item_definitions ARRAY, diagnostic_report_codes jsonb, healthcare_service_id, facility_id, deleted
```
- `emr_servicerequest.activity_definition_id` points here — join for the canonical test/procedure name.

### emr_device (Equipment: oxygen concentrators, monitors...)
```
id, identifier, status, availability_status, manufacturer, registered_name, user_friendly_name,
serial_number, lot_number, care_type, current_encounter_id, current_location_id,
facility_id, managing_organization_id, deleted
```

### emr_resourcecategory (Category tree for products/charge definitions)
```
id, resource_type, resource_sub_type, title, slug, is_child, parent_id, parent_cache ARRAY,
level_cache, facility_id, calculated_monetary_components jsonb, deleted
```

### Other tables (exist, rarely needed for reports)
`emr_availabilityexception` (schedule holidays), `emr_deviceencounterhistory` / `emr_devicelocationhistory` / `emr_deviceservicehistory`, `emr_facilitylocationorganization`, `emr_facilitymonetoryconfig`, `emr_formsubmission`, `emr_metaartifact`, `emr_observationdefinition`, `emr_specimendefinition`, `emr_questionnaireorganization` / `emr_questionnairefacilityorganization` / `emr_questionnaireresponsetemplate`, `emr_template`, `emr_tokencategory` / `emr_tokensubqueue`, `emr_resourcerequestcomment`, `emr_userresourcefavorites`, `emr_uservaluesetpreference`, `security_permissionmodel` / `security_rolepermission`, `facility_mobileotp`, `care_scribe_*` (AI scribe app), `care_notifications_*`. Verify columns with `information_schema` before using.

---

## COMMON PATTERNS

### Patient with Identifier (IMPORTANT: ALWAYS filter by config_id!)
```sql
-- ⚠️ WITHOUT config_id filter, you get multiple rows per patient (one per identifier type)
-- Ask user for config_id, or run: SELECT id, config->>'display' FROM emr_patientidentifierconfig WHERE deleted = false AND status = 'active'
LEFT JOIN emr_patientidentifier pi ON p.id = pi.patient_id 
    AND pi.deleted = false 
    AND pi.config_id = 21  -- ALWAYS specify config_id — ask user if unknown
LEFT JOIN emr_patientidentifierconfig pic ON pi.config_id = pic.id
-- Use: pi.value AS patient_id, pic.config->>'display' AS id_type
```

### Patient Tag Child from Parent (e.g., Zone, Area)
```sql
-- Gets the child tag display name where parent_id matches
-- e.g., if Zone is parent (id=55), this gets "Zone A", "Zone B" etc.
COALESCE(
    (SELECT et.display 
     FROM unnest(p.instance_tags) AS tag_id
     LEFT JOIN emr_tagconfig et ON et.id = tag_id
     WHERE et.parent_id = 55  -- hardcode after discovering with helper query
     LIMIT 1),
    'unassigned'
) AS tag_child_name
```

### User Full Name
```sql
TRIM(COALESCE(u.prefix || ' ', '') || u.first_name || ' ' || u.last_name, '') AS full_name
-- Or simpler:
TRIM(u.first_name || ' ' || u.last_name, '') AS full_name
```

### Latest Record Per Entity (e.g., latest bed per encounter)
```sql
SELECT DISTINCT ON (e.id)
    e.id,
    fle.created_date
FROM emr_encounter e
JOIN emr_facilitylocationencounter fle ON fle.encounter_id = e.id
ORDER BY e.id, fle.created_date DESC
```

### Encounter with Bed Location
```sql
JOIN emr_facilitylocationencounter fle ON fle.encounter_id = e.id AND fle.deleted = false
JOIN emr_facilitylocation fl ON fle.location_id = fl.id AND fl.deleted = false
WHERE fl.form = 'bd'  -- bd=bed, rm=room, wa=ward
AND fl.status = 'active'
```

### JSON Array Extraction (Questionnaires)

**⚠️ Clinical form concepts (mobility status, bedbound, home visit assessments, symptom scores) are NOT columns — they live in `emr_questionnaireresponse.responses` JSONB. Use the discovery workflow: find questionnaire → find question UUID → check answer values → build query.**

```sql
FROM emr_questionnaireresponse qr,
LATERAL jsonb_array_elements(qr.responses) AS r,
LATERAL jsonb_array_elements(r->'values') AS v
WHERE r->>'question_id' = '<uuid>'
-- Use: v->>'value'
```

**Questions nest recursively — groups inside groups, 3+ levels deep** (e.g. Nursing Care → Ryles Tube → Size). A flat 2-level query MISSES the deeper ones — always use the recursive `question_tree` discovery query (see "Find question UUIDs" in the discovery section) which flattens every level and shows the question number + path + answer options.

**Gotchas:**
- Same form exists as multiple questionnaire IDs (versions) — query with `IN (id1, id2, ...)`
- Answer values are UPPER_SNAKE_CASE (e.g., `BED_BOUND`, `AMBULATORY`) — if the query FILTERS by a specific answer, verify actual values first; skip verification when just listing/counting/grouping answers (values appear in results anyway)
- Use `DISTINCT ON (patient_id) ... ORDER BY patient_id, created_date DESC` for latest response per patient

### Date Filters
Date columns are `timestamptz` — **no typecast needed**, compare directly with date strings:
```sql
-- Direct comparison works fine (PostgreSQL auto-casts)
WHERE created_date >= '2026-01-01'
AND created_date < '2026-07-09'

-- With Metabase field filter (map variable to the date column in question settings):
[[AND {{date_filter}}]]

-- Common date columns per table:
-- emr_tokenbooking  → created_date (booking date), booked_on (appointment date)
-- emr_tokenslot     → start_datetime, end_datetime
-- emr_encounter     → period_start, period_end, created_date
-- emr_condition     → recorded_date, created_date
-- users_user        → date_joined
-- emr_invoice       → issue_date, modified_date
```

### Identifying Practitioner / Doctor for an Appointment
Practitioner is NOT directly on `emr_tokenbooking`. Follow this chain:
```
emr_tokenbooking → emr_tokenslot → emr_schedulableresource → users_user
```
```sql
JOIN emr_tokenslot ts ON tb.token_slot_id = ts.id AND ts.deleted = false
JOIN emr_schedulableresource sr ON ts.resource_id = sr.id AND sr.deleted = false
LEFT JOIN users_user u ON sr.user_id = u.id AND u.deleted = false
-- Display: TRIM(u.first_name || ' ' || COALESCE(u.last_name, '')) AS practitioner
-- Note: sr.user_id may be NULL if slot is for a healthcare service or location, not a person
```

**emr_schedulableresource columns:**
```
id                    bigint
user_id               bigint → users_user (NULL if not a person)
healthcare_service_id bigint
location_id           bigint
resource_type         varchar
facility_id           bigint
deleted               boolean
```

### Department of a Practitioner (e.g. appointments per department)
There is no department column on the user — membership lives in `emr_facilityorganizationuser`. Chain:
```
emr_schedulableresource.user_id → emr_facilityorganizationuser.user_id → emr_facilityorganization (org_type = 'dept')
```
```sql
JOIN emr_facilityorganizationuser ON emr_facilityorganizationuser.user_id = emr_schedulableresource.user_id
    AND emr_facilityorganizationuser.deleted = false
JOIN emr_facilityorganization ON emr_facilityorganizationuser.organization_id = emr_facilityorganization.id
    AND emr_facilityorganization.deleted = false
    AND emr_facilityorganization.org_type = 'dept'   -- without this you also get 'root' and 'team' memberships
-- Display: emr_facilityorganization.name AS department
```
⚠️ A user can belong to multiple departments — the same appointment may then appear under more than one department.

Don't confuse with the department of an **encounter** — that links directly via `emr_encounterorganization.encounter_id → organization_id → emr_facilityorganization` (no practitioner involved).

### Soft Delete (ALWAYS USE)
```sql
WHERE deleted = false
-- Apply to ALL tables in joins!
```

---

## HELPER QUERIES

### Find identifier config_id for your instance
```sql
SELECT id, config->>'display' as name, status
FROM emr_patientidentifierconfig 
WHERE deleted = false ORDER BY id;
```

### Find tag parent IDs (to use in tag child lookup)
```sql
SELECT id, display, parent_id, category
FROM emr_tagconfig
WHERE deleted = false AND parent_id IS NULL
ORDER BY id;
```

### Find child tags under a parent
```sql
SELECT id, display, parent_id FROM emr_tagconfig
WHERE deleted = false
ORDER BY parent_id, display;
```

### List facility locations (beds/rooms)
```sql
SELECT id, name, form, status, root_location_id, facility_id
FROM emr_facilitylocation
WHERE deleted = false
ORDER BY facility_id, form, name;
```

### List questionnaires
```sql
SELECT id, title, slug, status, subject_type
FROM emr_questionnaire
WHERE deleted = false AND status = 'active';
```

### List questions in a form
Use the recursive `question_tree` query from the discovery section ("Find question UUIDs") — forms nest groups inside groups, so flat queries miss questions.

---

## EXAMPLE QUERIES

### Patients with Diagnoses (with identifier and date filter)
```sql
SELECT 
    p.id AS patient_id,
    p.name AS patient_name,
    p.phone_number,
    pi.value AS patient_identifier,
    pic.config->>'display' AS identifier_type,
    c.code AS diagnosis_code,
    c.clinical_status,
    c.verification_status,
    c.severity,
    c.recorded_date,
    c.created_date
FROM emr_patient p
JOIN emr_condition c ON c.patient_id = p.id AND c.deleted = false
LEFT JOIN emr_patientidentifier pi ON p.id = pi.patient_id 
    AND pi.deleted = false
    AND pi.config_id = 21  -- ask user for correct config_id
LEFT JOIN emr_patientidentifierconfig pic ON pi.config_id = pic.id
WHERE p.deleted = false
AND c.created_date < '2026-07-09'
ORDER BY c.created_date DESC
```

### Patients with >5 Rescheduled Appointments (with tags)
```sql
SELECT 
    p.id AS patient_id,
    p.name AS patient_name,
    p.phone_number,
    pi.value AS patient_identifier,
    COALESCE(
        (SELECT et.display FROM unnest(p.instance_tags) AS tag_id
         LEFT JOIN emr_tagconfig et ON et.id = tag_id
         WHERE et.parent_id = 55 LIMIT 1),
        'unassigned'
    ) AS zone,
    COUNT(*) AS reschedule_count
FROM emr_tokenbooking tb
JOIN emr_patient p ON tb.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON p.id = pi.patient_id 
    AND pi.deleted = false
    AND pi.config_id = 21  -- ask user for correct config_id
WHERE tb.deleted = false AND tb.status = 'rescheduled'
GROUP BY p.id, p.name, p.phone_number, pi.value, p.instance_tags
HAVING COUNT(*) > 5
ORDER BY reschedule_count DESC
```

### IP Encounters with Bed Assignment
```sql
SELECT DISTINCT ON (e.id)
    p.name AS patient_name,
    pi.value AS patient_id,
    e.created_date AS admission_date,
    fl.name AS bed_name,
    fle.created_date AS bed_assigned_date
FROM emr_encounter e
JOIN emr_patient p ON e.patient_id = p.id
LEFT JOIN emr_patientidentifier pi ON p.id = pi.patient_id AND pi.config_id = 21
JOIN emr_facilitylocationencounter fle ON fle.encounter_id = e.id AND fle.deleted = false
JOIN emr_facilitylocation fl ON fle.location_id = fl.id AND fl.deleted = false
WHERE e.encounter_class = 'imp'
AND e.deleted = false
AND fl.form = 'bd'
AND fl.status = 'active'
ORDER BY e.id, fle.created_date DESC
```

### District-wise Count of Users in a Department
```sql
-- ⚠️ Rules:
-- 1. Use INNER JOINs throughout the facility → geo → district chain (LEFT JOINs cause inflated counts)
-- 2. Use users_user.is_active = TRUE (not deleted = false) for active user count
-- 3. Do NOT filter org_type on the facility org — use name ILIKE for flexibility
-- 4. Use geo.parent_cache to walk up to district (level_cache = 1)
SELECT
    COALESCE(district.name, 'Unassigned') AS district,
    COUNT(DISTINCT users_user.id) AS user_count
FROM emr_facilityorganizationuser
JOIN emr_facilityorganization
    ON emr_facilityorganizationuser.organization_id = emr_facilityorganization.id
   AND emr_facilityorganization.deleted = FALSE
JOIN users_user
    ON emr_facilityorganizationuser.user_id = users_user.id
   AND users_user.is_active = TRUE
JOIN facility_facility
    ON facility_facility.id = emr_facilityorganization.facility_id
   AND facility_facility.deleted = FALSE
JOIN emr_organization AS geo
    ON facility_facility.geo_organization_id = geo.id
JOIN emr_organization AS district
    ON (district.id = ANY(geo.parent_cache) OR district.id = geo.id)
   AND district.level_cache = 1
   AND district.deleted = FALSE
WHERE emr_facilityorganizationuser.deleted = FALSE
  AND LOWER(emr_facilityorganization.name) LIKE '%jak%'  -- adjust department name
  [[AND {{date_joined}}]]
GROUP BY district.name
ORDER BY user_count DESC
```
