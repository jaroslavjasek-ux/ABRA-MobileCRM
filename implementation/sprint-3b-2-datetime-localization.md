# Sprint 3B.2 — Date/time picker localization

**Status:** Analysis complete  
**Date:** 2026-06-09  
**Scope:** Task 2 — Slovak `DD.MM.YYYY` + 24h for date/time inputs. **No implementation.**

---

## 1. Executive summary

| Area | Current state | Target |
|------|---------------|--------|
| **Displayed dates in lists/detail** | ✓ `DD.MM.YYYY HH:mm` via `i18n/format.ts` + `sk-SK` | Already correct |
| **Follow-up `<input type="datetime-local">`** | ✗ Browser/OS locale (often `MM/DD/YYYY` + AM/PM on en-US Windows) | `09.06.2026 10:00` |
| **Other date pickers in app** | None found besides follow-up | N/A |

**Root cause:** `datetime-local` rendering is controlled by the **browser and OS**, not Mobile CRM `format.ts`. `lang="sk"` on `<html>` is insufficient on Chromium/Windows with en-US regional settings.

---

## 2. Inventory of date/time UI

| Location | Control | Format source | Slovak 24h? |
|----------|---------|---------------|:-----------:|
| **My Day** — today rows | Text (`formatTime`) | `Intl` `sk-SK`, `hour12: false` | ✓ |
| **My Day** — overdue rows | Text (`formatCalendarDate`) | `DD.MM.YYYY` | ✓ |
| **My Day** — header | Text (`formatDate`) | Long Slovak weekday | ✓ |
| **Activity detail** — schedule | Text (`formatScheduleRange`) | `DD.MM.YYYY HH:mm` | ✓ |
| **Firm activities** | Text (`formatDateTimeFull`) | `DD.MM.YYYY HH:mm` | ✓ |
| **Complete form** — follow-up Termín | `<input type="datetime-local">` | **Native picker** | ✗ (environment) |

**Search:** only one `datetime-local` in `src/MobileCrm.Web` (`ActivityDetailPage.tsx` line ~513). No `type="date"` or `type="time"` elsewhere.

---

## 3. Why `datetime-local` shows US format

### 3.1 HTML behaviour

- Value is always ISO-like: `YYYY-MM-DDTHH:mm` (internal).
- **Visible** format in the control depends on:
  - OS regional settings (primary on Windows)
  - Browser locale
  - `lang` / `lang` on `<input>` (limited support)

### 3.2 App configuration today

```2:2:src/MobileCrm.Web/index.html
<html lang="sk">
```

```1:3:src/MobileCrm.Web/src/i18n/format.ts
import type { LocaleId } from "@/i18n/types";

const DEFAULT_LOCALE: LocaleId = "sk-SK";
```

App **read-only** formatting uses `sk-SK` consistently. The **picker** does not.

### 3.3 Observed symptom

User on en-US Windows sees:

```
06/09/2026 10:00 AM
```

Expected:

```
09.06.2026 10:00
```

---

## 4. Requirements mapping

| Requirement | `format.ts` (display) | `datetime-local` (input) |
|-------------|:---------------------:|:------------------------:|
| DD.MM.YYYY | ✓ | ✗ |
| 24-hour time | ✓ | ✗ (AM/PM on en-US) |
| No AM/PM | ✓ | ✗ |
| Consistent with rest of app | ✓ | ✗ |

---

## 5. Recommended approaches (for implementation sprint)

### 5.1 Option A — Split controls (recommended for MVP fix)

Replace single `datetime-local` with:

| Control | Type | Notes |
|---------|------|-------|
| Dátum | `type="date"` or text + mask | Still locale-sensitive on some browsers |
| Čas | `type="time"` | Usually 24h when `lang=sk` |

Show **read-only preview** next to inputs using existing `formatDateTimeFull()` so user always sees `09.06.2026 10:00` regardless of native chrome.

**Pros:** Small diff, no new dependency, preview guarantees SK display.  
**Cons:** Two fields; native date may still vary.

### 5.2 Option B — Text input + Slovak mask

Single text field `placeholder="DD.MM.YYYY HH:mm"` with parse/format helpers mirroring `format.ts`.

**Pros:** Full control over display.  
**Cons:** Mobile keyboard UX; validation burden.

### 5.3 Option C — Custom picker component

Use a library (e.g. `react-day-picker` + time select) styled for mobile.

**Pros:** Best UX long-term.  
**Cons:** Larger scope; new dependency.

### 5.4 Option D — `datetime-local` + `lang` / `locale` hacks only

```html
<input type="datetime-local" lang="sk-SK" />
```

**Pros:** Minimal change.  
**Cons:** **Unreliable** on Windows Chromium; not sufficient alone.

### 5.5 Recommendation

**Option A** for Sprint 3B.3: split date/time + Slovak preview line using `formatDateTimeFull`. Reuse `followUpStartToIso` by combining date + time parts.

---

## 6. Implementation notes (future)

| File | Change |
|------|--------|
| `ActivityDetailPage.tsx` | Replace `datetime-local` |
| `followUpDefaults.ts` | Return separate default date + time or combined helper |
| `sk-SK.ts` | Labels: `followUpDate`, `followUpTime`, preview hint |
| `global.css` | Optional: style split row |

**API:** unchanged — still send ISO-8601 `scheduledStart`.

**Tests:** unit tests for parse/format round-trip `09.06.2026 10:00` ↔ ISO.

---

## 7. Verification checklist (post-fix)

1. Windows + en-US regional settings → user sees `09.06.2026 10:00` in preview or control.
2. iOS Safari SK → 24h, day-first.
3. Submitted ISO matches selected local instant (DST edge around midnight).
4. Activity detail schedule still `formatScheduleRange` after create.

---

## 8. Out of scope

- Localizing Gen desktop
- Firm search / other screens (no pickers today)
- ABRA Gen `SheduledStart$DATE` storage format (UTC instant — already correct)
