# CRM object validation — Mobile CRM vs ABRA Gen

**Reference mapping:** [`../../../analysis/domain/gen-business-object-mapping.md`](../../../analysis/domain/gen-business-object-mapping.md)  
**Inventory:** [business-object-inventory.md](business-object-inventory.md)  
**Server:** `http://localhost/demo` (DEMO instance, discovery 2026-06-04)

Validates each **Mobile CRM domain entity** against discovered Gen controllers. **Inferred Gen CRUD** comes from OpenAPI path shapes only. **Mobile CRM CRUD** is required product capability (Gen permissions may restrict actual writes).

**Status legend:** Confirmed | Candidate | Partial | Gap | N/A

---

## 1. Validation summary

| Status | Count |
|--------|------:|
| Confirmed | 6 |
| Candidate | 7 |
| Partial | 2 |
| Gap | 1 |
| N/A | 2 |

---

## 2. Entity validation table

### MVP — core

| Mobile CRM entity | Mapping expected (doc) | Gen object (validated) | Schema (OpenAPI) | Mobile CRM CRUD | Gen inferred CRUD | Status |
|-------------------|------------------------|-------------------------|------------------|-----------------|-------------------|--------|
| **Firm** | `Firm` | **firms** (firma) | `firm` | R | RCUD | **Confirmed** |
| **Contact** | TBD | **persons** (osoba); link via `FirmPersons` / `InitialFirmPerson_ID` | `person` | R | RCUD | **Candidate** |
| **Activity** | TBD | **crmactivities** (aktivita) | `crmactivity` | R, C, U | RCUD | **Confirmed** |
| **Activity type / status** | Enumerations | **crmactivitytypes**, **crmactivityareas**, **crmactivityqueues** | — | R | RCUD | **Confirmed** |
| **Sales representative** | TBD | **currentuser** (aktuálny používateľ); **securityusers**; **employees** | — | R | R (+ profile) | **Candidate** |
| **Commercial health signal** | Derived | **firms** fields + **monthfirminformations**; **firminsolvencyrecords**; **unreliablefirmlogs** | `firm`, … | R | R | **Partial** |
| **Pipeline snapshot** | TBD | **busorders** filtered by `Firm_ID` | `busorder` | R (optional) | RCUD | **Candidate** |
| **My Day** | — (composite) | **crmactivities** (+ no separate calendar BO) | — | — | — | **N/A** |
| **Authentication session** | Auth context | **currentuser** | — | C, R, U, D | R | **Candidate** |

### MVP — supporting (on Firm)

| Mobile CRM entity | Gen object (validated) | Mobile CRM CRUD | Status |
|-------------------|-------------------------|-----------------|--------|
| **Firm address** | Embedded **firms** (address fields TBD in schema) | R | **Candidate** |
| **Firm commercial status** | **firms** → `PMState_ID` | R | **Confirmed** |

### Phase 2

| Mobile CRM entity | Mapping expected | Gen object (validated) | Mobile CRM CRUD | Gen inferred CRUD | Status |
|-------------------|------------------|-------------------------|-----------------|-------------------|--------|
| **Sales opportunity** | TBD | **busorders** (zákazka); status enum **crmpipelinestatus** | R, C, U | RCUD | **Candidate** |
| **Calendar appointment** | TBD | No meeting BO; **crmactivities** dates (`StartDate$`, `PlannedEndDate$`) | R, C, U | RCUD | **Gap** (merged) |
| **Sales offer (Quote)** | TBD | **issuedoffers** (ponuka vydaná) | R, C, U (draft) | RCUD | **Confirmed** |
| **Sales order (Order)** | TBD | **issuedorders** (objednávka vydaná) — not `busorders` | R, C, U (draft) | RCUD | **Confirmed** |
| **Document line** | Nested lines | **issuedofferrows**, **issuedorderrows** (header nested pattern TBD) | R, C, U, D | via header | **Candidate** |
| **Product** | StoreCard | **storecards** (skladová karta); alt **crmproducts** | R | RCUD | **Confirmed** |
| **Price** | Derived | Line/header pricing on **issuedoffers** / **storecards** | R | R | **TBD** |
| **Stock availability** | Stock view | **storecards** (expand); no separate stock controller in CRM set | R | R | **TBD** |
| **Receivable position** | TBD | **issuedinvoices** + **firms** (`LimitAmount`, `BalanceAmount`, `AfterDueTerm*`) | R | R | **Partial** |

---

## 3. Dependencies (validated links)

| Mobile CRM entity | Depends on | Evidence in OpenAPI |
|-------------------|------------|---------------------|
| Activity | Firm | `crmactivities` → `Firm_ID` |
| Activity | Contact (optional) | `ResponsibleCustomerPerson_ID`, `Person_ID` |
| Activity | Sales opportunity (Phase 2) | `BusOrder_ID` on `crmactivities` |
| Activity | Sales representative | `ResponsibleUser_ID` |
| Activity | Activity type / status | `CRMActivityType_ID`, `CRMActivityArea_ID`, `CRMActivityQueue_ID` |
| Contact | Firm | `persons` → `FirmPersons`, `InitialFirmPerson_ID` |
| Pipeline snapshot / Opportunity | Firm | `busorders` → `Firm_ID` |
| Sales offer / order | Firm | Document headers → `Firm_ID` (validate per BO) |
| Document line | Offer / order header | Nested collections (validate 26+ header pattern) |
| Commercial health | Firm | Fields on `firm` schema |
| My Day | Activity | List queries on `crmactivities` |

---

## 4. Mobile CRM CRUD vs Gen permissions

| Entity | Mobile needs | Gen exposes (inferred) | Gap |
|--------|--------------|------------------------|-----|
| Firm | R | RCUD | Mobile must **not** use C/U/D (P-01) |
| Contact | R (MVP) | RCUD | MVP read-only by product; Gen may allow write |
| Activity | R, C, U | RCUD | Align Complete → PUT; delete optional |
| Opportunity | R, C, U (P2) | RCUD | Confirm posting rules in Gen |
| Quote / Order | R, C, U draft (P2) | RCUD | Posted docs read-only (P-05) |
| Commercial health | R | R on firm/finance | Field-level security TBD |

---

## 5. Open questions — OpenAPI validation backlog

Prioritised field- and behaviour-level checks on **`openapi/*.json`** and live sandbox.

### P0 — MVP blocker resolution

| ID | Entity | Question | Suggested spec |
|----|--------|----------|----------------|
| OQ-V-01 | Activity | Confirm schema name `crmactivity` vs `crmactivities` for POST body | `openapi/crmactivities.json` |
| OQ-V-02 | Activity | Mandatory fields for create and complete (validation) | `components/schemas` |
| OQ-V-03 | Activity | Filter fields for My Day: `ResponsibleUser_ID`, `StartDate$`, status | Live GET + `where` |
| OQ-V-04 | Firm | Search fields: `Name`, `ICO`, `Code`, `PMState_ID` | `openapi/firms.json` |
| OQ-V-05 | Firm | Commercial health: which of `LimitAmount`, `Insolvency*`, `Unreliable*`, `AfterDueTerm*` are populated for sales role | Permissions test |
| OQ-V-06 | Contact | List contacts for firm: expand `FirmPersons` on firm vs filter `persons` | Compare both |
| OQ-V-07 | Sales representative | Map login user → `ResponsibleUser_ID` (`currentuser` vs `securityusers`) | Auth spike |

### P1 — MVP optional / Phase 2 entry

| ID | Entity | Question |
|----|--------|----------|
| OQ-V-08 | Pipeline snapshot | Is `busorders` the pipeline deal? Confirm with business users (zákazka) |
| OQ-V-09 | Opportunity | `CRMPipelineStatus_ID` or similar on `busorder`? |
| OQ-V-10 | Activity | Link `BusOrder_ID` when logging visit against deal |
| OQ-V-11 | Calendar | Confirm no separate appointment BO; use activity schedule fields only |

### P2 — Phase 2 documents & catalogue

| ID | Entity | Question |
|----|--------|----------|
| OQ-V-12 | Quote / Order | Draft states: `issuedofferstates`, confirm transitions |
| OQ-V-13 | Document line | Lines only via header POST/PUT (26+); no `/issuedoffers/{id}/rows` |
| OQ-V-14 | Product | `storecards` vs `crmproducts` for mobile line picker |
| OQ-V-15 | Receivable | Overdue: query `issuedinvoices` vs firm `AfterDueTerm` |

### P3 — Resolved by this spike (update mapping doc)

| Mapping OQ | Resolution (DEMO) |
|------------|-------------------|
| OQ-FIRM-01 | Controller name: **firms** |
| OQ-ACT-01 | Primary activity BO: **crmactivities** |
| OQ-CONT-01 | Contact person BO: **persons** (not `contacts`) |
| OQ-OPP-01 | No `opportunities`; candidate **busorders** |
| OQ-OFF-01 | Quote: **issuedoffers** |
| OQ-ORD-01 | Order (sales): **issuedorders** (distinct from **busorders**) |
| OQ-PROD-01 | Product: **storecards** (+ **crmproducts** for CRM catalogue) |

---

## 6. Recommended updates to mapping document

After workshop sign-off, update [`gen-business-object-mapping.md`](../../../analysis/domain/gen-business-object-mapping.md):

| Entity | Replace TBD with |
|--------|------------------|
| Firm | `firms` |
| Activity | `crmactivities` |
| Contact | `persons` (+ firm link pattern from OQ-V-06) |
| Sales offer | `issuedoffers` |
| Sales order | `issuedorders` |
| Sales opportunity | `busorders` (candidate) |
| Product | `storecards` |
| Calendar appointment | Merged into `crmactivities` until BO found |

---

## 7. Document history

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-06-04 | Initial validation vs localhost DEMO OpenAPI |
