# Source — ABRA Mobile CRM

Sprint 0–1 implementation: **Login → Session → My Day**; **Customers** (firm search, firm detail, contact detail).

## Prerequisites

- [.NET 8 SDK](https://dotnet.microsoft.com/download)
- [Node.js 20+](https://nodejs.org/) (npm included)
- ABRA Gen DEMO (or TEST) reachable — copy `config/config.example.yaml` to `config/config.yaml`

## Run adapter

```powershell
cd D:\ABRA\ABRA-MobileCRM\src\MobileCrm.Adapter
# Set Gen password in appsettings.Development.json or user-secrets
dotnet run
```

Default URL: `http://localhost:5080`  
Health: `GET http://localhost:5080/health`

## Run web

```powershell
cd D:\ABRA\ABRA-MobileCRM\src\MobileCrm.Web
npm install
npm run dev
```

Open `http://localhost:5173` — Vite proxies `/api` to the adapter.

## Projects

| Project | Role |
|---------|------|
| `MobileCrm.Adapter` | `/api/v1` — session, my-day, firms, contacts, health |
| `MobileCrm.Adapter.Gen` | Gen HTTP client, mappers, firm/contact queries |
| `MobileCrm.Web` | React SPA — SCR-001–002, SCR-003–005, SCR-010 |

### Sprint 1 API (authenticated)

- `GET /api/v1/firms?q=` — search (min 2 chars)
- `GET /api/v1/firms/{firmId}` — firm 360° (contacts from `firmpersons`, best-effort recent activities)
- `GET /api/v1/contacts/{contactId}?firmId=` — contact detail
- `GET /api/v1/activities/{activityId}` — activity detail (SCR-006, read-only)

## Build solution

```powershell
cd D:\ABRA\ABRA-MobileCRM
dotnet build MobileCrm.sln
```
