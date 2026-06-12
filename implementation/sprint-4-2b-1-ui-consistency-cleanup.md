# Sprint 4.2B.1 — UI Consistency Cleanup

**Status:** Implemented  
**Date:** 2026-06-11  
**Scope:** Visual polish only — no API, backend, workflow, or business logic changes.

---

## 1. Goal

Unify typography, spacing, form controls, and section headers across Mobile CRM forms so Create Activity, Activity Detail actions, Login, and future screens share one design system.

---

## 2. Typography system

### Font family

```css
font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
```

Loaded via Google Fonts in `index.html`; applied globally through `--font-family`.

### Labels (`.field > span`, `.note-label`)

| Property | Value |
|----------|-------|
| `font-size` | `14px` (`--form-label-size`) |
| `font-weight` | `500` (`--form-label-weight`) |
| `line-height` | `20px` (`--form-label-line-height`) |
| `color` | `var(--color-text)` |

### Inputs / selects / textareas

| Property | Value |
|----------|-------|
| `font-size` | `16px` (`--form-input-size`) |
| `font-weight` | `400` (`--form-input-weight`) |
| `line-height` | `24px` (`--form-input-line-height`) |

Shared selector: `.form-control`, `.field input`, `.field select`, `.field textarea`, `.search-field input`, `.follow-up-schedule-date`, `.follow-up-schedule-time`.

### Helper text (`.hint`, `.form-helper`, `.follow-up-schedule-preview`)

| Property | Value |
|----------|-------|
| `font-size` | `12px` (`--form-helper-size`) |
| `line-height` | `16px` (`--form-helper-line-height`) |
| `color` | `var(--text-secondary)` |

---

## 3. Spacing system

| Token | Value | Usage |
|-------|-------|-------|
| `--form-spacing-sm` | `8px` | Label → control |
| `--form-spacing-md` | `20px` | Control → next field (`.form` gap) |
| `--form-spacing-lg` | `32px` | Section top padding (`.form-section`) |

### Vertical rhythm

```
Label
  ↓ 8px
Control
  ↓ 20px
Next label
...
Section border
  ↓ 32px padding-top
Section title
  ↓ 20px
Fields
```

---

## 4. Form controls

| Property | Value |
|----------|-------|
| `min-height` | `44px` (`--form-control-height`) |
| `border-radius` | `8px` (`--form-control-radius`) |
| `padding` | `10px 12px` |
| `border` | `1px solid var(--color-border)` |
| **Focus** | `2px solid var(--color-primary)` outline + border |
| **Select** | Custom chevron; consistent padding |

Textareas: same typography/border/focus; `min-height: 6rem`.

---

## 5. Section headers

Reusable classes:

| Class | Usage |
|-------|-------|
| `.form-section__title` | Form group titles (e.g. Obchodné väzby) |
| `.section-title` | Alias token (same styles) |
| `.detail-section h2` | Read-only detail cards (Termín, Poznámky, …) |

| Property | Value |
|----------|-------|
| `font-size` | `18px` (`--form-section-heading-size`) |
| `font-weight` | `600` |
| `line-height` | `28px` |

**Before:** Detail sections used `13px` uppercase muted labels; dimensions header used `0.95rem`.  
**After:** All section headings use the unified 18px / 600 style.

`.form-section` adds top border + `32px` padding for in-form groups.

---

## 6. Design tokens (`:root`)

```css
--font-family
--form-label-size
--form-input-size
--form-helper-size
--form-section-heading-size
--form-spacing-sm
--form-spacing-md
--form-spacing-lg
--form-control-height
--form-control-radius
--form-control-padding-x
--form-control-padding-y
--text-secondary
```

Future Sprint 4.3 screens should use `.form`, `.field`, `.form-section`, and these tokens.

---

## 7. Components / files updated

| File | Change |
|------|--------|
| `src/MobileCrm.Web/index.html` | Inter font preload |
| `src/MobileCrm.Web/src/styles/global.css` | Form design system, tokens, unified controls |
| `src/MobileCrm.Web/src/features/activities/CreateActivityPage.tsx` | `.form`, `.form-section`, `.form-section__title`; clear button → `.btn-clear` |
| `src/MobileCrm.Web/src/features/activities/ActivityDetailPage.tsx` | `.form` on note + complete forms |
| `src/MobileCrm.Web/src/features/login/LoginPage.tsx` | `.form` on login |

### Screens covered

| Screen | Form classes |
|--------|----------------|
| **Create Activity** | `.form`, `.form-section`, all `.field` controls |
| **Activity Detail — note** | `.form.activity-note-form` |
| **Activity Detail — complete / handover** | `.form.activity-complete-form` |
| **Login** | `.form.login-card` |
| **Firm search** | `.search-field input` (shared control styles) |
| **Detail sections** | Unified `h2` section headers |

---

## 8. Before / after (visual)

| Area | Before | After |
|------|--------|-------|
| Font | `system-ui` only | **Inter** + system fallbacks |
| Labels | Mixed `1rem` / implicit | **14px / 500** |
| Inputs | `1rem`, selects unstyled | **16px**, selects match inputs |
| Date preview | `0.9rem`, custom muted color | **12px** helper token |
| Obchodné väzby | `0.95rem` title, tight gap | **18px** section title, **32px** section spacing |
| Detail h2 | Uppercase `13px` muted | **18px / 600** primary text |
| Field spacing | `margin-top: 1rem`, `gap: 0.35rem` | **20px** / **8px** tokens |
| Clear firm button | `.btn-text` (white — wrong on form) | `.btn-clear` (primary link) |

### Screenshots

| Screenshot | Status |
|------------|--------|
| Create Activity — before | *Capture from pre-4.2B.1 branch if available* |
| Create Activity — after | *Capture `/app/activities/new`* |
| Activity Detail — complete form | *Capture in-progress activity* |
| Login | *Capture `/login`* |
| Mobile viewport (390px) | *Chrome DevTools* |

---

## 9. Regression checklist

| Check | Expected |
|-------|----------|
| Create Activity — all fields render | ✓ Same fields, unified style |
| Business dimensions section | ✓ `form-section` title + selects aligned |
| Date/time + preview helper | ✓ Same 12px helper under schedule |
| Complete + handover form | ✓ Textarea, checkbox, selects aligned |
| Login form | ✓ Labels + inputs match |
| Firm search input | ✓ Same control height/border |
| Detail page section headers | ✓ Larger unified titles (intentional) |
| Focus states | ✓ Primary blue outline on all controls |
| Mobile touch targets | ✓ 44px min height preserved |
| Build | ✓ `npm run build` passes |

---

## 10. Out of scope (unchanged)

- API / backend
- Form validation and submission logic
- Feature flags and dimension behaviour
- My Day list section headers (`.day-section` — list UI, not forms)

---

## 11. Usage guide (future forms)

```tsx
<form className="form" onSubmit={…}>
  <label className="field">
    <span>Label text</span>
    <input type="text" … />
  </label>
  <p className="hint">Optional helper</p>

  <section className="form-section">
    <h2 className="form-section__title">Section title</h2>
    <label className="field">…</label>
  </section>

  <button type="submit" className="btn-primary">Submit</button>
</form>
```
