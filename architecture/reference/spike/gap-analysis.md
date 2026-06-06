# Gap analysis — ABRA Gen discovery spike

**Inputs:** [business-object-inventory.md](business-object-inventory.md), [crm-object-validation.md](crm-object-validation.md), [domain model v0.2](../../../analysis/domain/business-domain-model.md)

**Environment:** `http://localhost/demo` — ABRA Gen DEMO (521 controllers). Results may differ per customer version and licence.

---

## 1. Executive summary

Discovery **succeeded** against the configured server. MVP core objects **Firm** (`firms`) and **Activity** (`crmactivities`) are **confirmed**. **Contact** maps to **persons** (not a `contacts` controller). Phase 2 **Quote** / **Order** map to **issuedoffers** / **issuedorders**.

Main gaps:

1. **Sales opportunity** — no `opportunities` controller; **busorders** (zákazka) is the strongest candidate and links to `crmactivities` via `BusOrder_ID`.
2. **Calendar appointment** — no dedicated meeting object in CRM-related set; **schedule lives on crmactivities** (D-09 → merged model for this deployment).
3. **Commercial health** — rich fields exist on **firms** but require field-level and permission validation for mobile exposure.
4. **Parallel task system** — **tasks** exists alongside **crmactivities**; Mobile CRM must not mix them in MVP.
5. **receivedorders** vs **issuedorders** — naming confusion; mobile “customer order” for seller is **issuedorders**, not received PO.

No application code was implemented; gaps below are **discovery / design** only.

---

## 2. Gap matrix

| # | Area | Domain expectation | Gen discovery | Severity | MVP / Phase |
|---|------|-------------------|---------------|----------|-------------|
| G-01 | Opportunity | Sales opportunity entity | **busorders** (zákazka), not named “opportunity” | Medium | P2 / optional snapshot |
| G-02 | Opportunity status | Pipeline stage | **crmpipelinestatus** (enum) + fields on **busorder** TBD | Medium | P2 |
| G-03 | Calendar | Separate appointment BO | **Not found**; holidays = generalcalendars | Medium | P2 |
| G-04 | Contact | Contact BO | **persons** + firm linkage pattern unclear | Medium | MVP |
| G-05 | Contact list | Contacts per firm | Need OQ-V-06 (expand vs filter) | Medium | MVP |
| G-06 | Commercial health | Derived signals | Fields on **firm** exist; overdue query TBD | Medium | MVP |
| G-07 | Receivable detail | ageing / balance | **issuedinvoices** + firm amounts; no single “receivable” BO | Low | P2 |
| G-08 | Sales rep identity | Employee for filters | **currentuser** vs **securityusers** vs **employees** | Medium | MVP |
| G-09 | Activity vs Task | Single interaction model | **crmactivities** AND **tasks** both RCUD | High | MVP |
| G-10 | Product picker | Product | **storecards** AND **crmproducts** | Low | P2 |
| G-11 | Document lines | Nested lines | Row controllers exist; must use **header** pattern on 26+ | Medium | P2 |
| G-12 | Auth ADR | Token model | **currentuser** present; bearer/basic from config only | Medium | MVP |
| G-13 | Gen version | 26+ rules | Sub-path deprecation not scanned on all 521 BOs | Low | All |
| G-14 | Environment | Production Gen | Spike run on **localhost DEMO** only | High | All |

---

## 3. MVP impact

| MVP capability | Status after spike | Action |
|----------------|-------------------|--------|
| M2 Firm search/detail | **Green** — `firms` | Field list OQ-V-04; commercial health OQ-V-05 |
| M3 Contacts | **Amber** — `persons` | Resolve OQ-V-06; UX for firm-scoped list |
| M4/M6 Activities / My Day | **Green** — `crmactivities` | OQ-V-01–03; ignore **tasks** |
| M5 Log visit | **Green** — POST/PUT `crmactivities` | OQ-V-02 validation rules |
| M1 Auth | **Amber** | OQ-V-07 + auth ADR |
| Commercial health on SCR-004 | **Amber** | OQ-V-05, OQ-V-15 subset |
| Pipeline snapshot (optional) | **Amber** | G-01 business confirmation |

---

## 4. Phase 2 impact

| Phase 2 entity | Status | Action |
|--------------|--------|--------|
| Pipeline / Opportunity | **Amber** — busorders | Validate stage fields; SCR-011/012 design |
| Quote | **Green** — issuedoffers | Draft states OQ-V-12 |
| Order | **Green** — issuedorders | Do not use busorders for order document |
| Calendar in My Day | **Red** — no BO | Use crmactivities schedule; revise Phase 2 calendar rows |
| Product / stock | **Amber** | OQ-V-14, OQ-V-15 |
| Receivable position | **Amber** | OQ-V-15 |

---

## 5. Domain model alignment

| Domain v0.2 decision | Spike outcome |
|----------------------|---------------|
| Firm = customer hub | **Aligned** (`firms`) |
| Activity = operational hub | **Aligned** (`crmactivities`) |
| Opportunity = commercial spine | **Needs rename** to Gen term **busorders** / Zákazka in docs |
| Calendar vs activity split | **Merged** on this server for scheduling |
| Quote/Order not primary hubs | **Aligned** — under firm/opportunity |
| Commercial health on firm | **Aligned** — implement from firm (+ invoices) |

---

## 6. Risks

| Risk | Mitigation |
|------|------------|
| Wrong BO for opportunity | Business workshop: confirm **busorders** = deal |
| Rep creates **tasks** instead of **crmactivities** | Product rules + UI labels “CRM activity” |
| Exposing finance fields | Role-based field mask; flags-only MVP (D-08) |
| Using deprecated sub-paths on documents | Apply ABRA 26+ header expand for lines (OQ-V-13) |
| DEMO ≠ production | Re-run discovery on staging/prod OpenAPI index |

---

## 7. Recommended next steps

| Priority | Action | Owner |
|----------|--------|-------|
| 1 | Close **OQ-V-06**, **OQ-V-07** (contact list + user mapping) | Integration spike |
| 2 | Live sandbox: create/complete **crmactivity** with `Firm_ID` | Integration spike |
| 3 | Workshop: **busorders** = opportunity? | Product + ERP |
| 4 | Update **gen-business-object-mapping.md** with confirmed names | Analysis |
| 5 | Re-run `discover_abra_gen_openapi.py` on staging | DevOps |
| 6 | Pin OpenAPI hash in `architecture/abra-gen-integration.md` version matrix | Architecture |

---

## 8. Artefacts produced

| Artefact | Path |
|----------|------|
| Full index (521) | `openapis-index.json` |
| CRM detail (80) | `crm-controllers-detail.json` |
| Raw OpenAPI | `openapi/*.json` |
| Discovery script | `scripts/discover_abra_gen_openapi.py` |
| Config | `config/config.yaml` (gitignored) |

---

## 9. Document history

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-06-04 | Initial gap analysis after discovery run |
