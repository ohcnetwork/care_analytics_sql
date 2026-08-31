# CARE Database Skill — REST API Edition

> AI reference for generating accurate SQL queries on Care HMIS database **and executing / saving them via the Metabase REST API** (no MCP required).

---

## Metabase Instance

| Property | Value |
|---|---|
| Base URL | `https://metabase.ohc.network` |
| Database ID | `3` |
| Auth header | `X-API-KEY: <key>` |

**API key is always provided by the user at the start of the session. Never hardcode it.**

---

## REST API Cheatsheet

### 1. Execute a native SQL query (test / preview)

```
POST https://metabase.ohc.network/api/dataset
Headers:
  Content-Type: application/json
  X-API-KEY: <key>

Body:
{
  "type": "native",
  "native": {
    "query": "<your SQL here>"
  },
  "database": 3
}
```

Response shape:
```json
{
  "data": {
    "rows": [ [...], [...] ],
    "cols": [ {"name": "col1", ...}, ... ],
    "rows_truncated": 2000
  },
  "error": null
}
```
- `data.rows` — array of value arrays
- `data.cols[i].name` — column names (parallel array)
- `error` — non-null string if query failed; always check before displaying results

### 2. List collections (to decide where to save)

```
GET https://metabase.ohc.network/api/collection
Headers:
  X-API-KEY: <key>
```

Returns an array of `{ id, name, slug, ... }` objects. Show to user and ask which collection to save into.

### 3. Save a question (native SQL card)

```
POST https://metabase.ohc.network/api/card
Headers:
  Content-Type: application/json
  X-API-KEY: <key>

Body:
{
  "name": "<Question title>",
  "display": "table",
  "visualization_settings": {},
  "dataset_query": {
    "type": "native",
    "native": {
      "query": "<your SQL here>"
    },
    "database": 3
  },
  "collection_id": <collection_id>   // null = top-level "Our analytics"
}
```

Response includes `{ "id": <card_id>, "name": "...", ... }` on success.

### 4. Update an existing question

```
PUT https://metabase.ohc.network/api/card/<card_id>
Headers:
  Content-Type: application/json
  X-API-KEY: <key>

Body: (only the fields you want to change)
{
  "dataset_query": {
    "type": "native",
    "native": { "query": "<updated SQL>" },
    "database": 3
  }
}
```

### 5. Get database schema info (verify table columns)

```
GET https://metabase.ohc.network/api/database/3/metadata
Headers:
  X-API-KEY: <key>
```

Or just run an `information_schema` query via `POST /api/dataset` as shown above — faster and more reliable.

---

## ⚠️ CRITICAL RULES FOR AI

1. **ALWAYS verify table columns** before writing queries — run `information_schema` via `/api/dataset`.
2. **ALWAYS use `deleted = false`** — All CARE tables have soft delete.
3. **"Patient ID" ALWAYS means `emr_patientidentifier.value`** — NOT the internal `emr_patient.id`. Filter by a specific `config_id` (instance-specific, always confirm with user).
4. **Patient identifier `config_id` is instance-specific** — must be discovered per deployment.
5. **Parent tag IDs are instance-specific** — discover them before filtering.
6. **Always check `error` field in `/api/dataset` response** — if non-null, report the SQL error and fix before showing results.
7. **Never hardcode the API key** — always ask the user at start of session.
8. **NEVER use table aliases.** Write full table names in every reference (`emr_patient.name`, not `p.name`). Exceptions with no table name of their own: LATERAL / `jsonb_array_elements` derived elements, CTE names, and column output aliases (`AS patient_name`).
9. **Multiple questionnaires with the same title** — if the lookup returns more than one row with the same/near-same title, list them (id + response count) and ask the user which one(s) to use. Never silently pick or merge.
10. **When mapping Metabase field filters (e.g., `{{date_filter}}`), the mapped field ID must belong to the same database as `dataset_query.database`.** If table names exist in multiple databases, always resolve both table ID and field ID by matching the database ID first.

---

## 🔍 Always Ask User For

| Query involves... | Ask user for... | Why? |
|---|---|---|
| Patient identifier | `config_id` | Differs per instance (e.g. 21 = SSMM, 4 = Pallium) |
| Tag filtering (zone, area) | `parent_id` of the tag category | Instance-specific |
| Facility-specific data | `facility_id` | To scope to correct facility |
| Questionnaire responses | Questionnaire ID + question UUID | Forms vary per deployment |
| Date filtering | Which date column to use | `created_date`, `recorded_date`, `date_joined`, etc. |
| Where to save in Metabase | Collection name / ID | Always list collections and let user pick |

If the user doesn't know a value, run the appropriate discovery query via `/api/dataset` and present results.

---

## Discovery Queries (run via POST /api/dataset)

**Patient identifier config_id:**
```sql
SELECT id, config->>'display' AS identifier_name, status
FROM emr_patientidentifierconfig
WHERE deleted = false AND status = 'active'
ORDER BY id;
```

**Facility ID:**
```sql
SELECT id, name FROM facility_facility
WHERE deleted = false AND is_active = true ORDER BY name;
```

**Tag parent_id (zones, areas, teams):**
```sql
SELECT id, name, slug, type FROM emr_tagconfig
WHERE deleted = false ORDER BY type, name;
```

**Questionnaire list (no table aliases):**
```sql
SELECT emr_questionnaire.id AS questionnaire_id,
       emr_questionnaire.title AS title,
       emr_questionnaire.slug AS slug,
       emr_questionnaire.subject_type AS subject_type,
       COUNT(emr_questionnaireresponse.id) AS responses
FROM emr_questionnaire
LEFT JOIN emr_questionnaireresponse
    ON emr_questionnaire.id = emr_questionnaireresponse.questionnaire_id
   AND emr_questionnaireresponse.deleted = false
WHERE emr_questionnaire.deleted = false
GROUP BY emr_questionnaire.id, emr_questionnaire.title, emr_questionnaire.slug, emr_questionnaire.subject_type
ORDER BY responses DESC;
```

**Full structure of all questionnaires (the `questions` JSONB column holds the entire form):**
```sql
-- emr_questionnaire.questions is a JSONB column containing the complete form structure
-- (groups + questions + nesting). Dump it directly — no need to pick an ID.
SELECT id, title, slug, subject_type, jsonb_pretty(questions) AS questions_json
FROM emr_questionnaire
WHERE deleted = false
ORDER BY title;
```

**Actual answer values for a question (no table aliases):**
```sql
SELECT answer_element->>'value' AS answer_value, COUNT(*) AS cnt
FROM emr_questionnaireresponse,
LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS response_element,
LATERAL jsonb_array_elements(response_element->'values') AS answer_element
WHERE emr_questionnaireresponse.questionnaire_id IN (<ids>)
  AND emr_questionnaireresponse.deleted = false
  AND response_element->>'question_id' = '<uuid>'
GROUP BY answer_element->>'value' ORDER BY cnt DESC;
```

---

## 🗺️ Concept → Location Map

| User asks about... | Data lives in... |
|---|---|
| Mobility, bedbound, homebound | `emr_questionnaireresponse.responses` (JSONB) |
| Clinical assessments, home visit forms | `emr_questionnaireresponse.responses` (JSONB) |
| Symptoms, pain scale, ECOG | `emr_questionnaireresponse.responses` (JSONB) |
| Diagnosis / conditions | `emr_condition` (`code` is JSONB) |
| Vitals, lab results | `emr_observation` |
| Appointments / token status | `emr_tokenbooking.status` |
| Zone / area / patient grouping | `emr_patient.instance_tags` (array) + `emr_tagconfig` |
| Patient hospital ID | `emr_patientidentifier.value` + `config_id` |
| District / panchayat / ward | `emr_organization` (`level_cache`: 0=state … 4=grama panchayat, 5=ward) |
| Departments / teams | `emr_facilityorganization` + `emr_facilityorganizationuser` |
| Bed occupancy | `emr_facilitylocation` (form='bd') + `emr_facilitylocationencounter` |
| Invoices / payments | `emr_invoice`, `emr_account` |
| Charge item category / requester / invoice link | `emr_chargeitem` + `emr_chargeitemdefinition` (`category_id`) + `emr_resourcecategory.title` + `users_user` (`created_by_id`/`updated_by_id`/`performer_actor_id`) + `emr_invoice` (`paid_invoice_id`) |

---

## Key Query Patterns

### Patient identifier join (no table aliases)
```sql
LEFT JOIN emr_patientidentifier ON emr_patient.id = emr_patientidentifier.patient_id
    AND emr_patientidentifier.deleted = false
    AND emr_patientidentifier.config_id = <confirmed_config_id>
LEFT JOIN emr_patientidentifierconfig ON emr_patientidentifier.config_id = emr_patientidentifierconfig.id
-- Display: emr_patientidentifier.value AS patient_id, emr_patientidentifierconfig.config->>'display' AS id_type
```

### Tag-based filtering (zone / area)
```sql
-- Find all children of a parent tag
WITH tag_tree AS (
    SELECT emr_tagconfig.id AS id FROM emr_tagconfig
    WHERE emr_tagconfig.parent_id = <confirmed_parent_id> AND emr_tagconfig.deleted = false
)
SELECT emr_patient.name AS patient_name, emr_tagconfig.name AS tag_name
FROM emr_patient
JOIN emr_tagconfig ON emr_tagconfig.id = ANY(emr_patient.instance_tags) AND emr_tagconfig.deleted = false
JOIN tag_tree ON emr_tagconfig.id = tag_tree.id
WHERE emr_patient.deleted = false;
```

### Geographic chain (facility → district)
```sql
INNER JOIN emr_organization AS facility_org ON facility_facility.geo_organization_id = facility_org.id AND facility_org.deleted = false
INNER JOIN emr_organization AS district_org ON district_org.id = ANY(facility_org.parent_cache)
    AND district_org.level_cache = 1 AND district_org.deleted = false
-- Note: emr_organization is joined to itself here, so distinct labels are required for the two roles.
```

### Latest questionnaire response per patient (no table aliases)
```sql
WITH latest AS (
    SELECT DISTINCT ON (emr_questionnaireresponse.patient_id)
        emr_questionnaireresponse.patient_id AS patient_id,
        answer_element->>'value' AS answer
    FROM emr_questionnaireresponse,
    LATERAL jsonb_array_elements(emr_questionnaireresponse.responses) AS response_element,
    LATERAL jsonb_array_elements(response_element->'values') AS answer_element
    WHERE emr_questionnaireresponse.questionnaire_id IN (<confirmed_ids>)
      AND emr_questionnaireresponse.deleted = false
      AND response_element->>'question_id' = '<confirmed_uuid>'
    ORDER BY emr_questionnaireresponse.patient_id, emr_questionnaireresponse.created_date DESC
)
```

---

## Known Gotchas

- Same form often has **multiple questionnaire IDs** (versions) — always use `IN (id1, id2, ...)`.
- Answer values are often `UPPER_SNAKE_CASE` (e.g. `BED_BOUND`) — always verify with a discovery query.
- `subject_type` tells you whether responses link via `patient_id` or `encounter_id`.
- `/api/dataset` returns max **2000 rows** by default; for full exports add `"parameters": [{"type": "number", "target": ["variable", ["template-tag", "limit"]], "value": 100000}]` or use pagination.
- API key scope: if the key belongs to a non-admin user, some collections may not be visible.
