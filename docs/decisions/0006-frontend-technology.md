# ADR 0006: Frontend technology — browser-based web application

**Status:** Accepted (revised)  
**Version:** 2.0.0  
**Date:** 2026-06-04  
**Supersedes:** ADR 0006 v1.0.0 (.NET MAUI decision)  
**Related:** [ADR 0002](0002-online-only-architecture.md) · [ADR 0005](0005-solution-architecture-v1.md) (amended) · [Solution Architecture v1.1](../../architecture/solution-architecture-v1.md) · [MVP scope](../../analysis/requirements/mvp-scope.md) · [Screen inventory v0.2](../../analysis/screens/README.md)

## Context

### Product constraint (hard)

**ABRA Mobile CRM is a browser-based web application.**

| Rule | Implication |
|------|-------------|
| Users access the product through a **mobile browser** | Mobile-first responsive web UX (SCR-001–010) |
| **Native mobile applications are out of scope** | .NET MAUI, React Native, Flutter, and store/MDM distribution do not apply |
| **PWA is acceptable** only as a **web enhancement** (manifest, install prompt, icons) — not as a native substitute | Optional `manifest.json` + service worker for shell; **not** an offline-sync platform for MVP |
| MVP is **online-only** ([ADR 0002](0002-online-only-architecture.md)) | No local business replica; SCR-009 on failure |
| **Offline is not a design driver** | Do not choose frontend stack for future SQLite/IndexedDB sync |
| **Per-customer deployment** unchanged | Customer hosts Gen + adapter; web UI hosted alongside or behind same origin |
| **ABRA Gen** remains sole source of truth ([ADR 0001](0001-abra-gen-source-of-truth.md)) | Browser calls **only** [`mobile-crm-api-v1`](../../architecture/mobile-crm-api-v1.md) |
| **ASP.NET Core adapter** and API contract **unchanged** | Thin BFF still implements `/api/v1` per [adapter mapping](../../architecture/mobile-crm-api-v1-adapter-mapping.md) |

ADR 0006 v1.0.0 compared React PWA to **.NET MAUI** and chose MAUI. That decision is **withdrawn** because native mobile is excluded by product policy.

---

## Invalidated arguments from ADR 0006 v1.0.0 (.NET MAUI)

The following rationales for MAUI **no longer apply** under the browser-only constraint. They are recorded so [ADR 0005](0005-solution-architecture-v1.md) and [Solution Architecture v1](../../architecture/solution-architecture-v1.md) can be corrected without losing audit trail.

### Based on native mobile assumptions

| Former MAUI argument | Why invalidated |
|----------------------|-----------------|
| Platform navigation patterns, `RefreshView`, native gestures | Web uses router + CSS/JS pull-to-refresh |
| App Store / Play / **enterprise MDM** distribution | Out of scope; URL + optional PWA install only |
| OS **Keychain / Keystore** for session token | Web uses `sessionStorage` / httpOnly cookie strategy (see §Decision) |
| App links, MDM managed configuration | Replaced by URL, optional PWA scope, runtime `config.json` |
| **FCM/APNs** push, biometrics, native camera/GPS permission models | Not MVP; not assumed for web unless explicit future ADR |
| MAUI simulator / emulator CI | Replaced by browser + Playwright |
| “Consistent iOS/Android **native** UX” | Replaced by **mobile-first web** UX on Safari/Chrome |

### Based on offline assumptions (or future offline as design driver)

| Former MAUI argument | Why invalidated |
|----------------------|-----------------|
| MAUI + **SQLite / EF Core** as credible **future offline** path | Offline is **not** a design driver; no stack choice for sync |
| PWA **IndexedDB / Service Worker offline-on-iOS unreliable** vs MAUI | Irrelevant while offline is out of scope |
| Comparison matrix row **“Future offline fit”** | Removed from browser-only evaluation |
| PWA offline cache as MVP differentiator | MVP is online-only; PWA SW limited to optional install/shell cache only |

### Based on future requirements outside MVP

| Former MAUI argument | Why invalidated |
|----------------------|-----------------|
| **Shared C#** DTO project with adapter as maintainability win | Nice-to-have; not required when OpenAPI generates TypeScript client |
| Single language (C#) across UI and adapter | Web frontend is TypeScript; adapter stays C# — acceptable split at API boundary |
| “ERP customers expect **installable native apps**” | Product mandates browser access |
| Phase 2 **same MAUI + adapter pattern** | Phase 2 extends **web SPA + adapter** |

### Arguments that **remain valid** (re-targeted to web)

| Argument | Web interpretation |
|----------|-------------------|
| All data via `/api/v1` only | Unchanged |
| Per-customer deploy, fast UI updates | **Stronger** for static web deploy |
| Online-only, SCR-008/009 error UX | Unchanged |
| Do not call Gen from client | Unchanged |
| Field-sales list/form screens | Mobile-first React UI |

---

## Options (browser-based only)

### Option A — React SPA + optional PWA enhancement

**React 18+** with **TypeScript**, built with **Vite**, styled for mobile-first (e.g. CSS modules or lightweight component library). Deployed as static files. Optional PWA: web app manifest, icons, minimal service worker (app shell cache only — **no** offline business sync).

```
Mobile browser  →  HTTPS (static SPA + /api/v1 proxy)  →  ASP.NET Core adapter  →  Gen
```

### Option B — Blazor WebAssembly (standalone SPA)

C# UI compiled to WebAssembly; static hosting like Option A. Shares language with adapter; heavier initial download on mobile networks.

### Option C — Blazor Server

UI rendered on server over SignalR. Persistent connection and server session state — **poor fit** for mobile browser field use (tab backgrounding, VPN drops, latency).

### Option D — Vue 3 SPA + optional PWA

Same architectural role as Option A; different framework ecosystem.

**Excluded from comparison (out of scope):** .NET MAUI, React Native, Flutter, native Kotlin/Swift.

---

## Evaluation (browser options, MVP-weighted)

| Criterion | React SPA (+PWA) | Blazor WASM | Blazor Server | Vue SPA (+PWA) |
|-----------|------------------|-------------|---------------|----------------|
| **Development effort** (10 SCR screens) | **++** Large ecosystem, mobile UI libs | **+** C# sharing; WASM tooling | **−** Server UI coupling | **++** Comparable to React |
| **Deployment** (per-customer static) | **++** `dist/` to IIS/nginx | **++** Same | **−** Needs always-on server UI | **++** Same as React |
| **Updates** | **++** Replace static files | **++** Same | **−** Server deploy for UI changes | **++** Same |
| **UX in mobile browser** | **++** Mature mobile CSS, touch targets | **+** Good; larger first payload | **−** Latency, disconnect | **++** Same class as React |
| **Device integration** (tel/mailto) | **++** Standard HTML | **++** Same | **++** Same | **++** Same |
| **Maintainability** | **++** OpenAPI → TS client; huge hiring pool | **+** OpenAPI → C# client; WASM/npm split | **−** Operational complexity | **++** Same as React |
| **Adapter contract alignment** | **++** No change to API v1 | **++** No change | **++** No change | **++** No change |
| **Online-only MVP** | **++** | **++** | **+** | **++** |
| **Minimize customer ops** | **++** Static only | **++** Static only | **−** Extra server role | **++** Static only |

**Blazor Server** is eliminated for MVP: violates simplicity on unreliable mobile browser connections.

**Blazor WASM** is viable for all-C# shops but adds **WASM download size** and slower first paint on 4G without offline benefit (not a driver).

**Vue vs React** is a team preference tie; both satisfy constraints.

---

## Decision

**Adopt Option A: React 18+ TypeScript SPA (Vite), with optional PWA enhancement** for MVP.

### Simplest maintainable web architecture (MVP)

```text
┌─────────────────────────────────────────────────────────────┐
│  Customer network                                           │
│  ┌──────────────┐   ┌─────────────────────────────────┐   │
│  │ Static web   │   │ ASP.NET Core thin adapter         │   │
│  │ (React dist) │   │ /api/v1  +  optional static host  │   │
│  │  or reverse  │──►│  or separate Kestrel port         │   │
│  │  proxy same  │   │         │                         │   │
│  │  origin      │   │         ▼                         │   │
│  └──────────────┘   │    ABRA Gen OpenAPI               │   │
│                     └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         ▲
         │ HTTPS (mobile browser)
    Field sales rep
```

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| **Presentation** | React + TypeScript + Vite | SCR-* routes, forms, lists, connectivity banner |
| **API access** | OpenAPI-generated **or** thin hand-written TS client | Only `/api/v1` |
| **Session** | `sessionStorage` for BFF Bearer token (MVP); prefer **httpOnly cookie** when adapter same-origin | No Gen password stored after login |
| **Routing** | React Router (or equivalent) | Maps to SCR-001–010 |
| **State** | React Query / TanStack Query (recommended) | Server state, cache-in-memory, pull-to-refresh |
| **PWA (optional)** | `vite-plugin-pwa` — manifest + install; SW caches app shell only | Not offline sync |
| **Hosting** | Adapter serves SPA **or** nginx/IIS static + reverse proxy `/api` → adapter | One customer URL |

**Not in MVP web stack:** Service Worker background sync, IndexedDB entity store, Blazor, native wrappers, Capacitor/Electron.

### PWA scope (explicit)

| In scope | Out of scope |
|----------|--------------|
| `manifest.json`, icons, `display: standalone` | Offline activity queue |
| Add-to-home-screen convenience | Stale business data in SW cache |
| Optional app-shell precache | Gen credential storage in browser beyond session token |

---

## Consequences

**Positive**

- Aligns with **browser-only** product vision.
- **Minimal customer deployment**: static UI artefact + existing adapter VM.
- **Fastest updates**: redeploy `dist/` without store/MDM.
- Unchanged **mobile-crm-api-v1** and **ASP.NET Core** adapter ([ADR 0005](0005-solution-architecture-v1.md) adapter row stands).
- CI: unit tests (Vitest) + E2E (Playwright mobile viewport).

**Negative**

- Two languages (TypeScript + C#) — mitigated by OpenAPI codegen from same contract.
- Session storage weaker than native keystore — mitigated by BFF session, short TTL, same-origin cookie path where possible.
- iOS Safari PWA limitations remain irrelevant for offline (not a driver); may affect install icon only.

**Actions**

- [ ] Amend [ADR 0005](0005-solution-architecture-v1.md) frontend row to React SPA (see amendment there).
- [ ] Update [Solution Architecture v1.1](../../architecture/solution-architecture-v1.md).
- [ ] Publish OpenAPI for `mobile-crm-api-v1` and generate TypeScript client.
- [ ] Document session storage threat model (replace NFR-S2 “keystore” wording for web in non-functional.md).
- [ ] Remove MAUI / store / MDM references from [mvp-scope](../../analysis/requirements/mvp-scope.md) open items when editing scope next.

**Supersedes:** ADR 0006 v1.0.0 (MAUI). **Amends:** [ADR 0005](0005-solution-architecture-v1.md) frontend decision only.

---

## Document history

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-06-04 | React PWA vs .NET MAUI — chose MAUI |
| 2.0.0 | 2026-06-04 | Browser-only product constraint; chose React SPA + optional PWA; invalidated MAUI rationales |
