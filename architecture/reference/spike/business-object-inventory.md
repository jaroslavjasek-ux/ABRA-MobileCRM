# ABRA Gen business object inventory

**Spike:** API discovery  
**Source:** `GET {base}/api-docs/openapis`  
**Environment:** `http://localhost/demo`  
**Discovered at (UTC):** 2026-06-04T14:16:51Z  
**Total controllers:** 521  

Each row is one **Web API controller** (= one Gen business object family in OpenAPI). Collection path follows controller name (e.g. `firms` → `/firms`).

---

## 1. Discovery method

| Step | Description |
|------|-------------|
| 1 | Load OpenAPI index from configured ABRA server |
| 2 | Exclude meta entry `openapi` (aggregate spec) |
| 3 | Classify **CRM-related** controllers by keyword match on `name` + `description` |
| 4 | For CRM subset (max 80), download OpenAPI JSON and infer collection CRUD from paths |
| 5 | Store raw exports under `openapi/` for field-level follow-up |

**Script:** `scripts/discover_abra_gen_openapi.py`

---

## 2. Summary statistics

| Metric | Count |
|--------|------:|
| All business objects (controllers) | 521 |
| CRM-related (keyword classification) | 88 |
| CRM subset with OpenAPI detail fetched | 80 |
| Fetch errors | 0 |

---

## 3. CRM-related business objects (88)

Alphabetical. **Inferred CRUD** = presence of list GET, POST, GET/PUT/DELETE by id on OpenAPI paths (not permission-tested).

| Controller | Description (Gen) | Inferred CRUD | Notes |
|------------|-------------------|:-------------:|-------|
| busorders | zákazka | RCUD | Candidate **pipeline / deal** |
| cdconfirmapproveds | schválený výdaj | RCUD | Credit approval |
| cdconfirms | požiadaviek na schválenie výdaje | RCUD | Credit approval |
| crmactivities | aktivita | RCUD | **MVP Activity** |
| crmactivityareas | oblasť aktivity | RCUD | Activity enum |
| crmactivityprocesses | proces aktivít | RCUD | Activity process |
| crmactivityqueues | rad aktivít | RCUD | Activity enum |
| crmactivitytypes | typ aktivít | RCUD | Activity enum |
| crmcampaignaudiences | CRM kampaň – cieľová skupina | RCUD | Marketing CRM |
| crmcampaignblacklists | CRM kampaň – blacklist | RCUD | Marketing CRM |
| crmcampaignfeedbacks | CRM kampaň – spätná väzba | RCUD | Marketing CRM |
| crmcampaignprocesses | CRM kampaň – proces | RCUD | Marketing CRM |
| crmcampaigns | CRM kampaň | RCUD | Marketing CRM |
| crmcampaigntypes | CRM kampaň – typ | RCUD | Marketing CRM |
| crmcampaignvariables | CRM kampaň – premenná | RCUD | Marketing CRM |
| crmmenuitems | položka CRM menu | RCUD | UI metadata |
| crmpipelinestatus | stav v pipe-line | RCUD | Pipeline **status** enum |
| crmproducts | produkt | RCUD | CRM product catalogue |
| crmprogresses | krok procesu | RCUD | Process step |
| currentuser | aktuálny používateľ | RCUD | **Auth / profile** |
| customsconfirmations | colné potvrdenie | RCUD | |
| dealercategories | kategória dealera | RCUD | |
| dealerdiscounts | zľava dealera | RCUD | |
| dealerturnoverdefinitions | definícia obratu dealera | RCUD | |
| docconfirmationbreaks | prerušenie schválenia dokladu | RCUD | |
| docconfirmationdefs | definícia schválenia dokladu | RCUD | |
| docconfirmations | schválenie dokladu | RCUD | |
| employeecountcategories | kategória počtu zamestnancov | RCUD | |
| employeeforeignstatus | zahraničný status zamestnanca | RCUD | |
| employees | zamestnanec | RCUD | HR / rep candidate |
| firminsolvencyrecords | záznam insolvencie firmy | RCUD | Commercial health |
| firms | firma | RCUD | **MVP Firm** |
| generalcalendars | platený sviatok | RCUD | Public holiday — not meeting |
| generalissuedorderrows | pohyby na rámcových zmluvách - nákup | RCUD | |
| generalissuedorders | rámcová zmluva - nákup | RCUD | |
| generalreceivedorderrows | pohyby na rámcových zmluvách - predaj | RCUD | |
| generalreceivedorders | rámcová zmluva - predaj | RCUD | |
| issueddepositinvoices | vydaná zálohová faktúra | RCUD | |
| issuedinvoicerows | pohyby na faktúrach vydaných | RCUD | |
| issuedinvoices | faktúra vydaná | RCUD | Receivables context |
| issuedofferfailurereasons | dôvod neúspechu ponuky | RCUD | |
| issuedofferrows | pohyby na ponukách vydaných | RCUD | Quote lines |
| issuedoffers | ponuka vydaná | RCUD | **Quote** |
| issuedofferstates | stav ponuky | RCUD | |
| issuedoffertypes | typ ponuky | RCUD | |
| issuedorderrows | pohyby na objednávkach vydaných | RCUD | Order lines |
| issuedorders | objednávka vydaná | RCUD | **Order (issued)** |
| logstoreaddresscodedefs | definícia kódu adresy skladu | RCUD | |
| monthfirminformations | mesačné údaje firmy | RCUD | Firm monthly / credit |
| ordersgenerations | generovanie objednávok | RCUD | |
| paymentorderrequests | požiadavka na platobný príkaz | RCUD | |
| paymentorders | platobný príkaz | RCUD | |
| pdmusers | používateľ modulu evidencie pošty | RCUD | |
| penaltyinvoices | penalizačná faktúra | RCUD | |
| personinsolvencyrecords | záznam insolvencie osoby | RCUD | |
| persons | osoba | RCUD | **Contact candidate** |
| plmjoborders | pracovný príkaz | RCUD | Manufacturing |
| plmjobordersnotices | oznámenie k pracovnému príkazu | RCUD | |
| plmworkers | pracovník PLM | RCUD | |
| posusers | používateľ pokladne | RCUD | |
| receiveddepositinvoices | prijatá zálohová faktúra | RCUD | |
| receivedinvoices | faktúra prijatá | RCUD | |
| receivedorderrows | pohyby na objednávkach prijatých | RCUD | |
| receivedorders | objednávka prijatá | RCUD | Customer PO (not mobile quote) |
| securityusers | používateľ | RCUD | **User / auth** |
| shiftcalendars | pracovný kalendár | RCUD | Workforce calendar |
| storecardcategories | kategória skladovej karty | RCUD | |
| storecards | skladová karta | RCUD | **Product** |
| taskattachmentdata | taskattachmentdata | RCUD | Task module |
| taskattachments | taskattachment | RCUD | |
| taskchanges | zmena úlohy | RCUD | |
| taskcomments | komentár úlohy | RCUD | |
| tasklists | tasklist | RCUD | |
| tasknotifications | tasknotification | RCUD | |
| taskrelations | vzťah úlohy | RCUD | |
| tasks | Úlohy | RCUD | Parallel task system (not MVP) |
| tasktags | tasktag | RCUD | |
| unreliablefirmlogfirms | firmy v logu nespoľahlivých | RCUD | Commercial health |
| unreliablefirmlogs | log nespoľahlivých firiem | RCUD | |
| userdefinedforms | definovateľný formulár | RCUD | |

---

## 4. Non-CRM objects (433)

Full alphabetical list is in machine-readable form: [`openapis-index.json`](openapis-index.json) (`controllers[].name`, `description`, `boclsid`, `ref`).

**Categories (illustrative, not exhaustive):**

| Domain | Example controllers |
|--------|---------------------|
| Accounting | `accountingevents`, `accountingstatements`, `vatdeclarations`, … |
| Assets / FM | `assets`, `assetmovements`, `fmacards`, … |
| Bank | `bankstatements`, `banktransactions`, … |
| Warehouse | `warehouses`, `warehousemovements`, `storecards` (also CRM) |
| HR / payroll | `payrolls`, `wages`, `attendances`, … |
| Manufacturing PLM | `plmorders`, `plmoperations`, … |

---

## 5. Objects explicitly not in index

| Expected by generic ERP | In this inventory |
|-------------------------|-------------------|
| Standalone `contacts` controller | **Not found** — use `persons` + firm link |
| `opportunities` controller | **Not found** — candidate `busorders` (zákazka) |
| `calendarappointments` | **Not found** — scheduling on `crmactivities` |

---

## 6. Document history

| Version | Date | Notes |
|---------|------|-------|
| 0.1 | 2026-06-04 | Initial discovery against localhost DEMO |
