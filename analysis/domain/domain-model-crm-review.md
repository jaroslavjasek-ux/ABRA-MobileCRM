# CRM perspective review — business domain model

**Reviews:** [`business-domain-model.md`](business-domain-model.md) v0.1  
**Date:** 2026-06-04  
**Constraint:** ABRA Gen remains the only source of truth; refinements change **conceptual model and navigation**, not ownership.

---

## Executive summary

The v0.1 model is **ERP-aligned** (firm master data, activities, documents) but **under-specified as CRM**: pipeline is late and weak, receivables are deferred too far, and Activity vs Calendar is left open in a way that will hurt daily usability.

Recommended direction:

1. Reframe navigation around **three hub types** (temporal, relationship, commercial) instead of two co-primary entities.
2. Elevate **sales opportunity** to the commercial spine in Phase 2 — above offers/orders as anchors.
3. Introduce **commercial health signals** on Firm in MVP (minimal) and expand receivables in Phase 2.
4. Split **scheduling (calendar)** from **selling (activity)** in the model, with an explicit link — and a unified **My Day** view that does not merge Gen records.

Refinements are applied in **business-domain-model.md v0.2**.

---

## 1. Primary navigation anchors

### What v0.1 does well

- **Firm** as relationship hub matches B2B field sales (“who am I visiting?”).
- **Activity** as temporal work list matches “what am I doing today?”
- Documents correctly demoted to firm context for Phase 2.

### CRM challenge

| Issue | Why it matters |
|-------|----------------|
| **Activity and Firm as co-primary entities** | Reps switch between *time-based* and *account-based* thinking. Two entity primaries force the product to pick a default tab without a clear CRM story. |
| **No pipeline hub** | Mature CRM navigation is **My Day · Accounts · Pipeline**. v0.1 jumps from activities to documents, skipping the deal spine. |
| **Offers/orders as Phase 2 primaries** | Documents are **outcomes** of selling, not where reps orient. Pipeline-first reps think in **opportunities**, not order headers. |
| **“Activity” overloaded** | Dashboard, visit log, and task compliance are one entity — fine for MVP, but the anchor should be the **My Day agenda**, not the data object name. |

### Refinement (Gen still truth)

| Hub type | Business name | MVP / Phase | Gen-backed content |
|----------|---------------|-------------|-------------------|
| **Temporal** | **My Day** | MVP | Open and completed **activities**; plus **calendar appointments** when Gen exposes them (unified agenda, separate records). |
| **Relationship** | **Firm** (customer) | MVP | Firm 360° — contacts, recent interactions, commercial signals. |
| **Commercial** | **Pipeline** (opportunities) | Phase 2 primary | **Sales opportunities** by stage; drill to firm and documents. |
| **Secondary** | Contact, Product, Document | As today | Reachable from Firm or Opportunity. |

**Anchor rule:** Users navigate by **hub purpose**, not by database object labels. Entities remain Gen-owned; hubs are **presentation groupings** of Gen data.

**Demotion:** Sales offer and sales order are **no longer primary anchors** — they sit under **Firm** or **Opportunity** depending on whether the deal record exists in Gen.

---

## 2. Opportunity placement

### What v0.1 does

- **Sales opportunity** listed in Phase 2 catalogue with “TBD” permissions.
- Not in relationship diagram as spine.
- Not a navigation anchor.

### CRM challenge

| Issue | Why it matters |
|-------|----------------|
| **Opportunity orphaned in Phase 2** | Without opportunity, Activity (effort) and Order (outcome) are disconnected — no **pipeline velocity**, forecast, or stage discipline. |
| **Documents before pipeline** | Offers/orders as primary anchors invert typical CRM: **opportunity → quote → order**. |
| **Firm-only selling story** | Account management CRM fits; **deal-driven** field sales needs opportunity on the path, even read-only at first. |

### Refinement

**Promote sales opportunity** to a **core commercial entity** (Phase 2), with explicit relationships:

| Relationship | Cardinality | Meaning |
|--------------|-------------|---------|
| Firm → Opportunity | 1 : N | Each deal belongs to one firm. |
| Opportunity → Activity | 1 : N | Calls and visits can support a specific deal. |
| Opportunity → Sales offer / order | 1 : N | Documents realise the opportunity. |
| Activity → Opportunity | N : 0..1 | Customer interaction optionally tied to one open deal. |

**MVP (no full pipeline UI):** Optional **firm-level pipeline snapshot** if Gen holds opportunities — e.g. count of open deals, highest-stage open opportunity name. Read-only, Gen-sourced, not a new entity. Workshop: confirm Gen CRM module.

**Phase 2:** **Pipeline** hub — list/filter opportunities (my / team per Gen permissions); stage update where Gen allows.

**Ownership unchanged:** Opportunity master data and stage rules live in Gen; Mobile CRM does not maintain a shadow pipeline.

---

## 3. Receivables visibility

### What v0.1 does

- **Receivable position** as Phase 2 entity, read-only on firm detail.
- Grouped with stock as “not an anchor.”

### CRM challenge

| Issue | Why it matters |
|-------|----------------|
| **Deferred to Phase 2** | Persona explicitly wants **receivables context** before visits; credit surprises on site damage trust and waste trips. |
| **Ledger-shaped entity** | Full receivable position is finance language; reps need **actionable visit signals** (can I sell? collect? escalate?). |
| **Detached from commercial story** | Receivables without opportunity context feels like collections; on CRM it should support **risk-aware selling**. |

### Refinement

Introduce **commercial health signal** (supporting concept, not a navigation anchor) — a **read-only Gen-derived view** on Firm:

| Signal (illustrative) | Business use | Typical MVP |
|-----------------------|--------------|-------------|
| **Firm commercial status** | Blocked / watch / active | Yes (already in model) |
| **Credit exposure level** | Traffic-light or within-limit flag | MVP if Gen permits read |
| **Overdue receivable indicator** | Any overdue balance yes/no or ageing bucket | MVP minimal; Phase 2 detail |
| **Open opportunity value** | Deal in flight vs risk | Phase 2 |

**Receivable position** remains the **Phase 2 detailed breakdown** (amounts, ageing, limit utilisation) — still Gen-owned, still read-only.

**Permission refinement:** Field sales **read** commercial health signals; **write** stays with finance in Gen (P-06 unchanged). Some organisations hide amounts but show **blocked for sales** flag — policy in Gen, reflected in CRM.

**Placement:** Always on **Firm** (relationship hub); optionally repeated on **Opportunity** when Gen ties credit check to deal.

**Not a hub:** Reps never “browse receivables”; they see **risk context while selling**.

---

## 4. Activity vs Calendar distinction

### What v0.1 does

- **Activity** = MVP core.
- **Calendar appointment** = optional Phase 2.
- D-01 left open (same object vs separate).

### CRM challenge

| Issue | Why it matters |
|-------|----------------|
| **Ambiguity creates duplicates** | Rep books Outlook/Gen calendar, then logs “visit” again — managers see two events or none tied. |
| **Single entity assumption** | If Gen uses one record, model must say so. If two, merging in UI without a **business link** breaks audit. |
| **My Day confusion** | Reps do not care which Gen object — they care **what happens at 10:00**. |

### Refinement — business definitions

| Concept | Business purpose | Typical Gen role |
|---------|------------------|------------------|
| **Calendar appointment** | **When and where** — time box, location, attendees, room/travel. Scheduling and reminders. | Calendar / appointment object |
| **CRM activity** | **Why and outcome** — customer interaction, subject, result, next step, link to firm/opportunity. Selling and compliance. | CRM activity / task object |

**Customer visit** in the field is often **both**: scheduled as appointment, **fulfilled by** activity with outcome.

### Relationship (when Gen has two objects)

| Link | Rule |
|------|------|
| Appointment → Activity | 0..1 fulfilment activity per customer-facing appointment |
| Activity → Appointment | 0..1 source appointment |
| Duplicate prevention | Completing visit should not require re-entering time if appointment exists |

**When Gen has a single object:** Model one **customer interaction** entity with **scheduling** and **outcome** aspects; do not invent a second Gen record.

### My Day (unified agenda)

| Row type | Source in Gen | Rep sees |
|----------|---------------|----------|
| Scheduled slot | Calendar appointment | Time, title, firm if linked |
| Selling task | CRM activity (open) | Due, firm, type |
| Overdue | CRM activity | Highlighted |

**MVP:** My Day driven by **activities** only until calendar is confirmed in Gen.  
**Phase 2:** Merge calendar appointments into same hub **without** merging underlying Gen entities.

**Permissions:** Calendar may be read-only on mobile while activities are writable — separate permission rows in matrix.

---

## 5. Summary of proposed changes to canonical model

| Area | v0.1 | v0.2 refinement |
|------|------|-----------------|
| Navigation | Activity + Firm co-primary | **My Day** + **Firm** (MVP); **Pipeline** (Phase 2); documents demoted |
| Opportunity | Phase 2 catalogue item | Commercial spine; links to activity & documents; optional firm snapshot MVP |
| Receivables | Phase 2 entity on firm | **Commercial health signals** (MVP minimal) + detailed receivable position Phase 2 |
| Activity vs Calendar | Undecided (D-01) | Distinct purposes + link; unified My Day view |

---

## 6. Workshop decisions enabled by this review

| ID | Question |
|----|----------|
| D-07 | Does Gen expose opportunities in this deployment? MVP firm snapshot yes/no? |
| D-08 | Which commercial health signals are reps allowed to see (amount vs flag only)? |
| D-09 | One or two Gen objects for visit scheduling vs outcome? |
| D-10 | Default home hub: My Day or Firm for this organisation? |

---

## Document history

| Version | Date | Change |
|---------|------|--------|
| 0.1 | 2026-06-04 | Initial CRM review |
