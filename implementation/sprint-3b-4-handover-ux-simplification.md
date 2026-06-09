# Sprint 3B.4 — Handover UX simplification

**Status:** Implemented  
**Date:** 2026-06-08  
**Depends on:** [3B.3 workflow polish](sprint-3b-3-workflow-polish.md), [3B follow-up source context](sprint-3b-followup-source-context.md)

---

## 1. Goal

Simplify the activity handover workflow for mobile field work. Users should enter outcome text **once** (`Nový výsledok`) when completing with follow-up — not duplicate information in a separate follow-up **Popis** field.

No new business functionality. UX simplification only.

---

## 2. Before / after

### Before (3B.3)

Complete form with **Naplánovať ďalší krok** enabled:

| Field | Required | Purpose |
|-------|----------|---------|
| Nový výsledok | Yes | Completion outcome → source `Answer` |
| Predmet | Yes | Follow-up subject |
| Termín | Yes | Follow-up schedule |
| Priradený používateľ | Yes | Assignee |
| **Popis** | No | Follow-up `Description` (optional) |

Users often typed similar text in **Nový výsledok** and **Popis**, or left **Popis** empty and lost the source brief on the child.

### After (3B.4)

Follow-up section shows only:

| Field | Required |
|-------|----------|
| Predmet | Yes |
| Termín | Yes |
| Priradený používateľ | Yes |

**Popis** is removed from the UI. Child activity text fields are set automatically on the server.

---

## 3. Inherited Description behaviour

Implemented in Sprint 3B.3 (`ActivityMapper.ResolveFollowUpTextFields` + `ActivityCreateService`). Unchanged in 3B.4 — the UI no longer sends `followUp.description`.

| Source `Description` | Child `Description` after handover |
|----------------------|-------------------------------------|
| `Kontrola kvality zákazky` | `Kontrola kvality zákazky` (copied) |
| *(empty)* | *(empty)* |

**Rule:** When the client omits follow-up description, the adapter inherits the source activity `Description` from the Gen GET performed during create.

**Not copied from Nový výsledok:** Completion outcome goes to source `Answer` (append), then the full source `Answer` history is copied to the child — see below.

---

## 4. Answer / history (unchanged)

| Step | Behaviour |
|------|-----------|
| Notes during visit | Prepended to source `Answer` |
| Complete — Nový výsledok | Appended to source `Answer` |
| Follow-up create | Full source `Answer` copied to child `Answer` |

Assignee sees complete conversation history on the new activity without retyping.

---

## 5. End-to-end workflow

```
Open activity
  → Add note          (source Answer)
  → Complete          (Nový výsledok → source Answer)
  → Naplánovať ďalší krok
      Predmet + Termín + Priradený používateľ
  → Save

Child activity:
  Description = source Description (if any)
  Answer      = source Answer history (notes + outcome)
```

**User types text once:** `Nový výsledok` only.

---

## 6. Changes made

| File | Change |
|------|--------|
| `ActivityDetailPage.tsx` | Removed follow-up **Popis** textarea, state, and `followUp.description` from API payload |
| Backend | **No change** — inheritance already correct |

API `followUp.description` remains optional on `PUT …/complete` for future/advanced clients; mobile web no longer sends it.

---

## 7. Verification

### Automated

| Check | Result |
|-------|--------|
| `npm run build` (MobileCrm.Web) | Pass |
| `ActivityMapperFollowUpContextTests` (inherit rules) | Pass |
| `ActivityMapperAppendAnswerTests` | Pass |

### Regression checklist

| Scenario | Expected |
|----------|----------|
| Complete without follow-up | Unchanged |
| Complete + follow-up, source has Description | Child inherits Description |
| Complete + follow-up, source Description empty | Child Description empty |
| Notes + complete outcome | Child Answer contains full history |
| Assign another user | Assignment unchanged (3B.1) |
| Follow-up visible in assignee My Day | Unchanged (3B.3 default schedule) |

### Manual UI

1. Open in-progress activity with existing **Popis** on detail.
2. Enable **Naplánovať ďalší krok**.
3. Confirm form shows **Predmet**, **Termín**, **Priradený používateľ** only — no **Popis**.
4. Enter **Nový výsledok**, submit.
5. Open follow-up → **Popis** matches source; **Odpoveď** shows inherited history.

---

## 8. Out of scope

Sprint 4.0 entities (Business Case, Work Order, Project, Activity Area/Type/Series) — not started.

---

## 9. References

- [sprint-3b-followup-source-context.md](sprint-3b-followup-source-context.md) — Description/Answer inheritance rules
- [sprint-3b-3-workflow-polish.md](sprint-3b-3-workflow-polish.md) — follow-up defaults and Slovak datetime UX
