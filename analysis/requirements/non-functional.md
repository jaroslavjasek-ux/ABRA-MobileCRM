# Non-functional requirements

## Performance

| ID | Requirement | MVP target |
|----|-------------|------------|
| NFR-P1 | Firm search results on good 4G | &lt; 3 s p95 (TBD measurement) |
| NFR-P2 | Firm detail load | &lt; 5 s p95 |
| NFR-P3 | Pagination for large firm lists | Required |

## Availability & connectivity

| ID | Requirement |
|----|-------------|
| NFR-A1 | Core flows require ABRA Gen reachable |
| NFR-A2 | UI shows explicit offline / timeout state; no silent data loss |
| NFR-A3 | Retry with backoff for idempotent reads only |

## Security

| ID | Requirement |
|----|-------------|
| NFR-S1 | Credentials not in source control |
| NFR-S2 | BFF session token in browser session storage or httpOnly cookie — not Gen password after login |
| NFR-S3 | Least-privilege Gen user per sales role |
| NFR-S4 | Audit trail remains in Gen (native logging) |

## Usability

| ID | Requirement |
|----|-------------|
| NFR-U1 | One-thumb primary actions on key screens |
| NFR-U2 | Czech or Slovak UI copy (TBD) |
| NFR-U3 | Accessible contrast for outdoor use |

## Maintainability

| ID | Requirement |
|----|-------------|
| NFR-M1 | OpenAPI version and Gen build documented per environment |
| NFR-M2 | Documentation updated with each scope change |

## Compliance

| ID | Requirement |
|----|-------------|
| NFR-C1 | GDPR: personal data processed only via Gen policies |
| NFR-C2 | Device loss: remote wipe via MDM (organisational) |
