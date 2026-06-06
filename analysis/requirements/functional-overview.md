# Functional overview

Capability map for Mobile CRM. **MVP** items link to [`mvp-scope.md`](mvp-scope.md).

## Customer & contact

| Capability | MVP | Gen alignment |
|------------|-----|---------------|
| Firm search (name, ICO, code) | Yes | `Firm` collection query |
| Firm detail (address, credit flags) | Yes | `GET` + `select` / `expand` |
| Contact list & detail | Yes | Linked to firm |
| Contact create/edit | No | Phase 2 |

## Activities & visits

| Capability | MVP | Gen alignment |
|------------|-----|---------------|
| Today / overdue list | Yes | Query TBD |
| Log visit with notes | Yes | Create/update BO TBD |
| Calendar integration | No | Phase 2 |

## Sales documents

| Capability | MVP | Gen alignment |
|------------|-----|---------------|
| View open offers/orders | No | Phase 2 |
| Create mobile order draft | No | Phase 2 |
| Stock / price check | No | Phase 2 |

## System

| Capability | MVP | Gen alignment |
|------------|-----|---------------|
| Login / session | Yes | Identity + API token |
| Health / connectivity indicator | Yes | N/A |
| Push notifications | No | Phase 2 |

Update **Gen alignment** column as objects are confirmed in [`../../architecture/abra-gen-integration.md`](../../architecture/abra-gen-integration.md).
