# Sprint 3A P0 — Follow-up activity create spike

**Run (UTC):** 2026-06-06T08:28:30.854365+00:00
**Base URL:** http://localhost/demo

## Source context (completed activity)

```json
{
  "ID": "2000000101",
  "DisplayName": "PrHo-1/2006",
  "Subject": "otázka na pozáručný servis",
  "Status": 2,
  "Firm_ID": "3000000101",
  "Person_ID": null,
  "ActivityType_ID": "2000000101",
  "ResponsibleUser_ID": null,
  "SolverUser_ID": "1300000101",
  "CreatedBy_ID": "1300000101",
  "SheduledStart$DATE": "2006-09-21T22:00:00.000Z"
}
```

## Scenario results

### A_minimal_no_source_refs

- Validate errors: **4** `['actqueue_id', 'period_id', 'solverrole_id', 'division_id']`
- Commit HTTP: **400**
- Persisted (GET): **False**
- ID: `None`
- DisplayName: `None`

**Validate payload:**
```json
{
  "Subject": "Sprint 3A follow-up test (minimal)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-08T10:00:00.000Z",
  "Description": "P0 spike — safe to delete"
}
```

**Commit payload:**
```json
{
  "Subject": "Sprint 3A follow-up test (minimal)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-08T10:00:00.000Z",
  "Description": "P0 spike — safe to delete",
  "ActivityArea_ID": "2000000101",
  "Period_ID": "3F80000101",
  "FirmOffice_ID": "3000000101"
}
```

### B_source_refs_no_owner

- Validate errors: **0** `[]`
- Commit HTTP: **201**
- Persisted (GET): **True**
- ID: `F100000101`
- DisplayName: `PrHo-8/2006`

**Validate payload:**
```json
{
  "Subject": "Sprint 3A follow-up test (source refs, no owner)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-08T10:00:00.000Z",
  "Description": "P0 spike — safe to delete"
}
```

**Commit payload:**
```json
{
  "Subject": "Sprint 3A follow-up test (source refs, no owner)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-08T10:00:00.000Z",
  "Description": "P0 spike — safe to delete",
  "ActQueue_ID": "2000000101",
  "Period_ID": "4000000101",
  "Division_ID": "2000000101",
  "SolverRole_ID": "1000000101",
  "ActivityArea_ID": "2000000101"
}
```

### C_source_refs_session_owner

- Validate errors: **0** `[]`
- Commit HTTP: **201**
- Persisted (GET): **True**
- ID: `H100000101`
- DisplayName: `PrHo-9/2006`

**Validate payload:**
```json
{
  "Subject": "Sprint 3A follow-up test (source refs + session owner)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-08T10:00:00.000Z",
  "Description": "P0 spike — safe to delete",
  "ResponsibleUser_ID": "2610000101",
  "SolverUser_ID": "2610000101"
}
```

**Commit payload:**
```json
{
  "Subject": "Sprint 3A follow-up test (source refs + session owner)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-08T10:00:00.000Z",
  "Description": "P0 spike — safe to delete",
  "ResponsibleUser_ID": "2610000101",
  "SolverUser_ID": "2610000101",
  "ActQueue_ID": "2000000101",
  "Period_ID": "4000000101",
  "Division_ID": "2000000101",
  "SolverRole_ID": "1000000101",
  "ActivityArea_ID": "2000000101"
}
```

### D_source_refs_inherited_owner

- Validate errors: **0** `[]`
- Commit HTTP: **201**
- Persisted (GET): **True**
- ID: `J100000101`
- DisplayName: `PrHo-10/2006`

**Validate payload:**
```json
{
  "Subject": "Sprint 3A follow-up test (source refs + inherited owner)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-08T10:00:00.000Z",
  "Description": "P0 spike — safe to delete",
  "ResponsibleUser_ID": "1300000101",
  "SolverUser_ID": "1300000101"
}
```

**Commit payload:**
```json
{
  "Subject": "Sprint 3A follow-up test (source refs + inherited owner)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-08T10:00:00.000Z",
  "Description": "P0 spike — safe to delete",
  "ResponsibleUser_ID": "1300000101",
  "SolverUser_ID": "1300000101",
  "ActQueue_ID": "2000000101",
  "Period_ID": "4000000101",
  "Division_ID": "2000000101",
  "SolverRole_ID": "1000000101",
  "ActivityArea_ID": "2000000101"
}
```

### E_commit_with_validation_flag

- Validate errors: **0** `[]`
- Commit HTTP: **200**
- Persisted (GET): **False**
- ID: `None`
- DisplayName: `None`

**Validate payload:**
```json
{
  "Subject": "Sprint 3A follow-up test (validate-only commit control)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-08T10:00:00.000Z",
  "Description": "P0 spike — safe to delete",
  "ResponsibleUser_ID": "2610000101",
  "SolverUser_ID": "2610000101"
}
```

**Commit payload:**
```json
{
  "Subject": "Sprint 3A follow-up test (validate-only commit control)",
  "Firm_ID": "3000000101",
  "ActivityType_ID": "2000000101",
  "SheduledStart$DATE": "2026-06-08T10:00:00.000Z",
  "Description": "P0 spike — safe to delete",
  "ResponsibleUser_ID": "2610000101",
  "SolverUser_ID": "2610000101",
  "ActQueue_ID": "2000000101",
  "Period_ID": "4000000101",
  "Division_ID": "2000000101",
  "SolverRole_ID": "1000000101",
  "ActivityArea_ID": "2000000101"
}
```

## Findings summary

- **Successful scenario:** B_source_refs_no_owner
- **Resulting ID:** `F100000101`
- **Resulting document number (DisplayName):** `PrHo-8/2006`
- **Merge validate → commit required:** True
- **Source reference fields required (ActQueue, Period, …):** True
- **ResponsibleUser_ID required for My Day:** False
- **Document number auto-generated:** True
- **Visible in My Day ownership query:** True

## Recommended Sprint 3A follow-up DTO

See `follow-up-activity-create-results.json` → `recommended_dto` (appended by spike runner if success).

**Raw log:** [`follow-up-activity-create-results.json`](follow-up-activity-create-results.json)
