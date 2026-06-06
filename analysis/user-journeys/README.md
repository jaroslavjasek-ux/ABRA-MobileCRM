# User journeys

Document end-to-end flows as markdown files: `UJ-###-short-name.md`.

## Template

```markdown
# UJ-###: Title

**Persona:** Field sales representative  
**MVP:** Yes | No  
**Preconditions:** User authenticated, online

## Steps
1. ...
2. ...

## Success criteria
- ...

## Gen touchpoints
| Step | API / BO |
|------|----------|
| 1 | ... |

## Exceptions
- Offline → show banner, block write
```

## Planned journeys (MVP)

| ID | Title | Screens | Status |
|----|-------|---------|--------|
| UJ-001 | Morning agenda — My Day | SCR-002, SCR-006 | Planned |
| UJ-002 | Find firm and open detail before visit | SCR-003, SCR-004, SCR-005 | Planned |
| UJ-003 | Log visit outcome | SCR-004, SCR-006, SCR-007 | Planned |

Screen specs: [`../screens/README.md`](../screens/README.md).

Add journey files under this folder as workshops complete.
