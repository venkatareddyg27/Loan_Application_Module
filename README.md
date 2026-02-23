# Loan Application API

A personal loan API that takes a borrower from credit check all the way through to money in their account. The borrower fills in a guided step-by-step form, a lender picks up the application from a shared pool and decides, then the admin sends the approved amount via bank transfer or UPI.

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Setup & Installation](#setup--installation)
5. [Application Flow](#application-flow)
6. [Entity Relationship Diagram](#entity-relationship-diagram)
7. [API Endpoints](#api-endpoints)
8. [Loan Calculator Logic](#loan-calculator-logic)
9. [Application Status Lifecycle](#application-status-lifecycle)
10. [Enums & Allowed Values](#enums--allowed-values)
11. [Error Handling](#error-handling)
12. [Business Rules](#business-rules)

---

## Overview

This API manages the full lifecycle of a personal loan for an NBFC — credit check, multi-step application form, lender review, and disbursement through a mock NBFC payment gateway.

| What | Details |
|---|---|
| Loan range | ₹5,000 – ₹20,000 |
| Tenures | 3, 6, 9, or 12 months |
| Interest rate | 12% per annum (flat) |
| Processing fee | 5% of the loan + 18% GST on that fee |
| Eligibility check | Credit score — must be 650 or above to qualify |
| References required | 2 people, both OTP-verified |
| Payout modes | Bank transfer / UPI |

---

## Tech Stack

| Layer | Technology | What it does |
|---|---|---|
| Framework | FastAPI | Handles HTTP requests, auto-generates Swagger docs at `/docs` |
| ORM | SQLAlchemy | Lets us work with database records as Python objects |
| Database | PostgreSQL | Stores everything (database name: `loan`) |
| Validation | Pydantic v2 | Checks incoming requests have the right shape and types |
| Auth | python-jose (JWT) | Verifies who is calling the API via Bearer token |
| Table creation | `Base.metadata.create_all` | Creates all tables automatically when the server starts |
| Runtime | Python 3.10 + uvicorn | ASGI server that runs the app |

---

## Project Structure

```
Loan_application/
├── .env                                  # Database connection string
└── app/
    ├── main.py                           # App entry point — registers all routers
    ├── core/
    │   ├── config.py                     # Reads SECRET_KEY, ALGORITHM, DATABASE_URL
    │   ├── deps.py                       # JWT dependency — extracts current user from token
    │   ├── enums.py                      # All fixed value sets: statuses, steps, purposes, relations
    │   ├── session.py                    # DB engine, session factory, get_db() dependency
    │   ├── mock_nbfc.py                  # Simulates Bank and UPI payment transfers
    │   ├── reference_generator.py        # Generates the 8-character loan reference number
    │   └── utils/
    │       └── enum_utils.py             # Small helpers for working with enums
    │
    ├── db_models/                        # SQLAlchemy table definitions — one file per table
    │   ├── __init__.py
    │   ├── user_profiles.py              # Borrower KYC — name, PAN, Aadhaar, income
    │   ├── loan_eligibility.py           # Result of the credit score check
    │   ├── loan_application.py           # Central table — ties everything together ★
    │   ├── loan_application_purpose.py   # Why the borrower needs the loan
    │   ├── loan_application_references.py       # The two people vouching for the borrower
    │   ├── loan_application_references_otp.py   # OTP records for reference mobile verification
    │   ├── loan_application_declaration.py      # Borrower's legal consents
    │   ├── loan_application_steps.py            # Tracks which steps have been completed
    │   ├── loan_disbursements.py         # Records of money sent out
    │   ├── lender.py                     # NBFC lender companies
    │   └── user_bank_details.py          # Borrower's bank account / UPI for receiving money
    │
    ├── repositories/                     # All DB queries — services call these, not the DB directly
    │   ├── base_repo.py
    │   ├── loan_application_repo.py
    │   ├── loan_application_purpose_repo.py
    │   ├── loan_application_reference_repo.py
    │   ├── loan_application_declaration_repo.py
    │   ├── loan_disbursement_repo.py
    │   └── loan_eligibility_repo.py
    │
    ├── routers/                          # Route definitions — thin layer, just calls services
    │   ├── loan_eligibility_router.py
    │   ├── loan_application_router.py
    │   ├── loan_application_purpose_router.py
    │   ├── loan_application_reference_router.py
    │   ├── reference_otp_router.py
    │   ├── loan_application_declaration_router.py
    │   ├── loan_application_summary_router.py
    │   ├── lender_router.py
    │   └── loan_disbursement_router.py
    │
    ├── schemas/                          # Pydantic models — what the API accepts and returns
    │   ├── base.py
    │   ├── loan_eligibility_schema.py
    │   ├── loan_application.py
    │   ├── loan_application_purpose.py
    │   ├── loan_application_references.py
    │   ├── loan_application_references_otp.py
    │   ├── loan_application_declaration.py
    │   ├── loan_application_steps.py
    │   ├── loan_application_summary.py
    │   ├── loan_disbursement_schema.py
    │   ├── loan_predisbursement_schema.py
    │   └── lender.py
    │
    └── services/                         # Business logic — the real work happens here
        ├── loan_eligibility_service.py   # Checks credit score, returns ELIGIBLE or REJECTED
        ├── loan_application_service.py   # Creates app, handles submit, locks on submission
        ├── loan_application_purpose_service.py
        ├── loan_application_reference_service.py
        ├── loan_application_declaration_service.py
        ├── loan_application_summary_service.py
        ├── loan_application_validation.py        # Pre-submit checks — all steps done?
        ├── loan_application_lock_manager_service.py  # Locks the app after submission
        ├── loan_calculator.py            # EMI formula, processing fee, net disbursement
        ├── loan_disbursement_service.py  # Calls the payment gateway, records result
        ├── pre_disbursement_service.py   # Preview of charges before money is sent
        └── reference_otp_service.py      # Generates, sends, and validates OTPs
```

---

## Setup & Installation

### 1. Configure Environment

```env
# .env
DATABASE_URL = "postgresql://postgres:1234@localhost:5432/loan"
```

### 2. Install Dependencies

```bash
cd Loan_application
python -m venv venv

# Activate virtualenv
source venv/bin/activate          # macOS/Linux
venv\Scripts\activate             # Windows

pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose[cryptography] pydantic
```

### 3. Run the Server

```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> Tables are created automatically on startup via `Base.metadata.create_all(bind=engine)` — no separate migration step needed.

### 4. Access API Docs

| URL | Description |
|---|---|
| `http://127.0.0.1:8000/docs` | Swagger UI — try every endpoint interactively |
| `http://127.0.0.1:8000/redoc` | ReDoc — clean read-only reference |

---

## Application Flow

The journey has three phases. Each step must be completed in order — the `step_tracker` table enforces the sequence and the `next_step` field in every response tells the client where to go.

---

### Phase 1 — Borrower fills in the application

```
 BORROWER          ROUTER                    SERVICE               DATABASE
    │                 │                          │                      │
    │── POST ────────▶│ /loan/eligibility/check  │                      │
    │  {user_profile_id,                         │                      │
    │   credit_score} │─────────────────────────▶│ LoanEligibilityService
    │                 │                          │                      │
    │                 │                          │  credit_score >= 650?│
    │                 │                          │  YES → ELIGIBLE      │
    │                 │                          │  NO  → REJECTED      │
    │                 │                          │─────────────────────▶│
    │                 │                          │   INSERT loan_eligibility
    │◀─ {eligibility_id, status, max_amount} ────│                      │
    │                 │                          │                      │
    │  ══ STEP 1 — LOAN DETAILS ═══════════════════════════════════════ │
    │                 │                          │                      │
    │── POST ────────▶│ /loan/application/apply  │                      │
    │  {user_profile_id,                         │                      │
    │   eligibility_id,                          │                      │
    │   tenure_months}│─────────────────────────▶│ LoanApplicationService
    │                 │                          │  .apply_loan()       │
    │                 │                          │                      │
    │                 │                          │  approved_amount is  │
    │                 │                          │  pulled from the     │
    │                 │                          │  eligibility record  │
    │                 │                          │  (not user input)    │
    │                 │                          │─────────────────────▶│
    │                 │                          │   INSERT loan_application
    │                 │                          │   status = DRAFT     │
    │                 │                          │   INSERT step_tracker
    │                 │                          │   loan_details = done│
    │◀─ {application_id, approved_amount, next_step: "PURPOSE"} ───────│
    │                 │                          │                      │
    │  ══ STEP 2 — PURPOSE ════════════════════════════════════════════ │
    │                 │                          │                      │
    │── PUT ─────────▶│ /loan/application/{id}/purpose                  │
    │  form-data:     │  (application/x-www-form-urlencoded)            │
    │  purpose_code,  │─────────────────────────▶│ PurposeService       │
    │  purpose_desc   │                          │─────────────────────▶│
    │                 │                          │   UPSERT purpose     │
    │                 │                          │   purpose_completed = True
    │◀─ {purpose_code, purpose_description} ─────│                      │
    │                 │                          │                      │
    │  ══ STEP 3 — REFERENCES + OTP (do for both ref1 and ref2) ══════ │
    │                 │                          │                      │
    │── PUT ─────────▶│ /loan/application/{id}/references               │
    │  form-data:     │  (application/x-www-form-urlencoded)            │
    │  ref1_name,     │─────────────────────────▶│ ReferenceService     │
    │  ref1_mobile,   │                          │─────────────────────▶│
    │  ref1_relation, │                          │   UPSERT 2 references│
    │  ref2_...       │                          │                      │
    │◀─ [{id, name, mobile, is_verified: false}, ...] ─────────────────│
    │                 │                          │                      │
    │── POST ────────▶│ /references/send-otp     │                      │
    │  {reference_id} │─────────────────────────▶│ ReferenceOTPService  │
    │                 │                          │─────────────────────▶│
    │                 │                          │   INSERT otp record  │
    │◀─ {message: "OTP sent"} ───────────────────│                      │
    │                 │                          │                      │
    │── POST ────────▶│ /references/verify-otp   │                      │
    │  {reference_id, │─────────────────────────▶│   validates OTP code │
    │   otp_code}     │                          │─────────────────────▶│
    │                 │                          │   UPDATE is_verified = True
    │◀─ {verified: true, verified_at} ───────────│                      │
    │                 │                          │                      │
    │  ══ STEP 4 — DECLARATION ════════════════════════════════════════ │
    │                 │                          │                      │
    │── PUT ─────────▶│ /loan/application/{id}/declaration              │
    │  {agreed_terms, │─────────────────────────▶│ DeclarationService   │
    │   consent_*,    │                          │─────────────────────▶│
    │   terms_version}│                          │   INSERT declaration │
    │                 │                          │   declaration_completed = True
    │◀─ {consent_timestamp, ...} ────────────────│                      │
    │                 │                          │                      │
    │  ══ STEP 5 — SUMMARY & SUBMIT ═══════════════════════════════════ │
    │                 │                          │                      │
    │── GET ─────────▶│ /loan/application/{id}/summary                  │
    │                 │─────────────────────────▶│ SummaryService       │
    │                 │                          │   checks all steps done
    │◀─ {user, loan_details, purpose, references,                       │
    │    declaration, can_submit: true} ─────────│                      │
    │                 │                          │                      │
    │── POST ────────▶│ /loan/application/{id}/submit                   │
    │  {confirm: true}│─────────────────────────▶│ LoanApplicationService
    │                 │                          │   validate all steps │
    │                 │                          │   calculate EMI+fees │
    │                 │                          │   generate ref number│
    │                 │                          │   lock the app       │
    │                 │                          │─────────────────────▶│
    │                 │                          │   UPDATE loan_application
    │                 │                          │   status = SUBMITTED │
    │                 │                          │   is_submitted = True│
    │                 │                          │   reference_number   │
    │                 │                          │   monthly_emi        │
    │                 │                          │   processing_fee     │
    │                 │                          │   gst_amount         │
    │                 │                          │   total_repayment    │
    │◀─ {reference_number, message, "24 hours"} ─│                      │
```

Borrower's job is done. The application appears in the lender's pool.

---

### Phase 2 — Lender reviews and decides

```
 LENDER            ROUTER                    SERVICE               DATABASE
    │                 │                          │                      │
    │── GET ─────────▶│ /lender/applications     │                      │
    │                 │─────────────────────────▶│ LenderService        │
    │                 │                          │   status=SUBMITTED   │
    │                 │                          │   lender_id=null     │
    │◀─ [{application_id, reference_number,      │                      │
    │     approved_amount, tenure, submitted_at}]│                      │
    │                 │                          │                      │
    │  Lender picks one to review                │                      │
    │                 │                          │                      │
    │── POST ────────▶│ /lender/pick/{id}?lender_id={id}               │
    │                 │─────────────────────────▶│   lender must be     │
    │                 │                          │   active + not blocked
    │                 │                          │                      │
    │                 │                          │   SELECT FOR UPDATE  │
    │                 │                          │   (row-level lock —  │
    │                 │                          │   two lenders cannot │
    │                 │                          │   claim same app)    │
    │                 │                          │─────────────────────▶│
    │                 │                          │   UPDATE lender_id = lender.id
    │                 │                          │   status = UNDER_REVIEW
    │◀─ {message: "Application picked"} ─────────│                      │
    │                 │                          │                      │
    │── GET ─────────▶│ /lender/my-applications/{lender_id}             │
    │◀─ [all apps assigned to this lender] ──────│                      │
    │                 │                          │                      │
    │  After reviewing the borrower's details:   │                      │
    │                 │                          │                      │
    │── POST ────────▶│ /lender/approve/{id}?lender_id={id}             │
    │                 │─────────────────────────▶│   must be UNDER_REVIEW
    │                 │                          │   must be same lender│
    │                 │                          │─────────────────────▶│
    │                 │                          │   status = APPROVED  │
    │◀─ {message: "Application approved"} ───────│                      │
    │                 │                          │                      │
    │           — OR —│                          │                      │
    │                 │                          │                      │
    │── POST ────────▶│ /lender/reject/{id}?lender_id={id}              │
    │                 │   &rejection_reason=...  │                      │
    │                 │─────────────────────────▶│   must be UNDER_REVIEW
    │                 │                          │   reason required    │
    │                 │                          │─────────────────────▶│
    │                 │                          │   status = REJECTED  │
    │◀─ {message: "Application rejected"} ───────│                      │
```

---

### Phase 3 — Admin disburses the money

```
 ADMIN             ROUTER                    SERVICE               DATABASE
    │                 │                          │                      │
    │  Only after lender sets status to APPROVED │                      │
    │                 │                          │                      │
    │── GET ─────────▶│ /admin/disbursement/{id} │                      │
    │                 │   (preview charges)      │                      │
    │◀─ {approved_amount, processing_fee,        │                      │
    │    gst_amount, net_disbursement_amount} ───│                      │
    │                 │                          │                      │
    │── POST ────────▶│ /admin/disbursement/{id} │                      │
    │  {payment_mode: │─────────────────────────▶│ LoanDisbursementService
    │   BANK | UPI}   │                          │   finds borrower's   │
    │                 │                          │   verified payout    │
    │                 │                          │   MockNBFCPaymentGateway
    │                 │                          │     .transfer_bank() │
    │                 │                          │     .transfer_upi()  │
    │                 │                          │─────────────────────▶│
    │                 │                          │   INSERT disbursement│
    │                 │                          │   status = DISBURSED │
    │◀─ {payment_status: SUCCESS,                │                      │
    │    payment_reference_id, amount} ──────────│                      │
```

---

## Entity Relationship Diagram

```
┌──────────────────┐          ┌──────────────────────────┐
│  user_profiles   │          │     loan_eligibility     │
│──────────────────│          │──────────────────────────│
│ PK  id           │──────────│ PK  id                   │
│     auth_user_id │  1:many  │ FK  user_profile_id      │
│     full_name    │          │     eligibility_status   │
│     dob          │          │     credit_score_used    │
│     email        │          │     max_eligible_amount  │
│     address      │          │     failure_reason       │
│     monthly_income          │     latest_checked_at    │
│     aadhaar_number          └──────────────┬───────────┘
│     pan_number   │                         │ 1:many
│     kyc_status   │                         │
│     pan_status   │                         ▼
│     profile_status          ┌────────────────────────────────────────┐
└────────┬─────────┘          │      loan_application  ★ (Central)    │
         │ 1:many             │────────────────────────────────────────│
         └───────────────────▶│ PK  id                                 │
                              │ FK  user_profile_id                    │
                              │ FK  eligibility_id                     │
                              │ FK  lender_id  (null until lender picks)
                              │     reference_number  VARCHAR(8)       │
                              │     approved_amount   NUMERIC(12,2)    │
                              │     requested_tenure_months            │
                              │     interest_rate     NUMERIC(5,2)     │
                              │     monthly_emi       NUMERIC(12,2)    │
                              │     processing_fee    NUMERIC(10,2)    │
                              │     gst_amount        NUMERIC(10,2)    │
                              │     total_repayment   NUMERIC(14,2)    │
                              │     current_step      VARCHAR(50)      │
                              │     application_status  ENUM           │
                              │     is_submitted       BOOLEAN         │
                              │     rejection_reason  VARCHAR(255)     │
                              │     ip_address        VARCHAR          │
                              │     created_at / updated_at            │
                              │     submitted_at / approved_at         │
                              │     rejected_at / disbursed_at         │
                              └──┬──────┬──────┬──────┬──────┬────────┘
                                 │      │      │      │      │
                            1:1  │ 1:1  │ 1:1  │ 1:2  │1:many│
                                 │      │      │      │      │
              ┌──────────────────▼┐ ┌───▼────┐ │  ┌───▼──┐ ┌▼──────────────┐
              │ loan_application  │ │ step_  │ │  │ ref. │ │disbursements  │
              │ _purpose          │ │ tracker│ │  │──────│ │───────────────│
              │───────────────────│ │────────│ │  │PK id │ │ PK  id        │
              │ FK/PK app_id      │ │FK/PK   │ │  │FK    │ │ FK  app_id    │
              │ purpose_code ENUM │ │app_id  │ │  │app_id│ │     amount    │
              │ purpose_desc      │ │loan_   │ │  │name  │ │ payment_mode  │
              └───────────────────┘ │details │ │  │mobile│ │ payment_status│
                                    │purp_   │ │  │relat.│ │ reference_id  │
                                    │refs_   │ │  │is_   │ │ initiated_at  │
                                    │decl_   │ │  │emerg.│ │ completed_at  │
                                    │curr_   │ │  │is_   │ └───────────────┘
                                    │step    │ │  │vrf.  │
                                    └────────┘ │  └──┬───┘
                                               │     │ 1:many
                                               │     ▼
                                               │  ┌──────────────────┐
                                               │  │ reference_mobile │
                                               │  │ _otp             │
                                               │  │──────────────────│
                                               │  │ PK  id           │
                                               │  │ FK  reference_id │
                                               │  │     otp_code     │
                                               │  │     is_used      │
                                               │  │     expires_at   │
                                               │  └──────────────────┘
                                               │
                             ┌─────────────────▼───┐
                             │ loan_application_    │
                             │ declaration          │
                             │──────────────────────│
                             │ PK  id               │
                             │ FK  application_id   │
                             │     agreed_terms      │
                             │     consent_credit_  │
                             │     check            │
                             │     consent_data_    │
                             │     sharing          │
                             │     has_existing_    │
                             │     loans            │
                             │     has_credit_card  │
                             │     has_default_     │
                             │     history          │
                             │     terms_version    │
                             │     ip_address       │
                             │     consent_timestamp│
                             │     is_locked        │
                             └─────────────────────┘

┌──────────────────┐     ┌──────────────────────┐
│    lenders       │     │   user_bank_details  │
│──────────────────│     │──────────────────────│
│ PK  id           │     │ PK  id               │
│     company_name │     │ FK  user_profile_id  │
│     gst_number   │     │     account_number   │
│     address      │     │     ifsc_code        │
│     is_active    │     │     account_holder   │
│     is_verified  │     │     upi_id           │
│     is_blocked   │     │     payment_mode     │
└──────────────────┘     │     is_verified      │
                         └──────────────────────┘
```

---

## API Endpoints

### Eligibility

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/loan/eligibility/check` | Run a credit score check. Returns eligible or rejected, plus the maximum loan amount the borrower can get. |
| `GET` | `/loan/eligibility/{eligibility_id}` | Fetch a previous eligibility result by its ID. |

**Request:**
```json
{
  "user_profile_id": 1,
  "credit_score": 720
}
```

**Response — eligible:**
```json
{
  "id": 1,
  "eligibility_status": "ELIGIBLE",
  "max_eligible_amount": 100000.00,
  "credit_score_used": 720,
  "failure_reason": null
}
```

**Response — rejected:**
```json
{
  "id": 2,
  "eligibility_status": "REJECTED",
  "max_eligible_amount": 0,
  "credit_score_used": 580,
  "failure_reason": "Credit score 580 is below the minimum required score of 650"
}
```

---

### Loan Application

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/loan/application/apply` | Start a new application. The approved amount comes from the eligibility record, not from the borrower. |
| `GET` | `/loan/application/{application_id}` | Check the current status and step. |
| `POST` | `/loan/application/{application_id}/submit` | Final submission — locks the application and generates a reference number. |

**Request — Apply:**
```json
{
  "user_profile_id": 1,
  "eligibility_id": 1,
  "requested_tenure_months": 12
}
```

**Response — Apply:**
```json
{
  "application_id": 42,
  "approved_amount": "10000.00",
  "next_step": "PURPOSE"
}
```

**Request — Submit:**
```json
{ "confirm": true }
```

**Response — Submit:**
```json
{
  "reference_number": "LA7X9P2Q",
  "message": "Loan application submitted successfully",
  "expected_decision_time": "24 hours"
}
```

---

### Purpose

| Method | Endpoint | Content-Type | Description |
|---|---|---|---|
| `PUT` | `/loan/application/{id}/purpose` | **form-data** | Save the reason for the loan. |
| `GET` | `/loan/application/{id}/purpose` | — | Get the saved purpose. |

>  This endpoint uses `application/x-www-form-urlencoded`, **not JSON**.

**Form fields:**
```
purpose_code=MEDICAL&purpose_description=Hospital surgery expenses
```

---

### References

| Method | Endpoint | Content-Type | Description |
|---|---|---|---|
| `PUT` | `/loan/application/{id}/references` | **form-data** | Save both references at once. |
| `GET` | `/loan/application/{id}/references` | — | Get both references and their OTP verification status. |

>  This endpoint uses `application/x-www-form-urlencoded`, **not JSON**.

**Form fields:**
```
ref1_name=John Doe
ref1_mobile_number=9876543210
ref1_relation_type=FRIEND
ref1_is_emergency_contact=true
ref2_name=Jane Smith
ref2_mobile_number=9876543211
ref2_relation_type=COLLEAGUE
ref2_is_emergency_contact=false
```

---

### Reference OTP

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/loan/application/references/send-otp` | Send an OTP to a reference's mobile number. |
| `POST` | `/loan/application/references/verify-otp` | Verify the OTP the reference received. |

Do this for both references — neither can be skipped.

**Send OTP:**
```json
{ "reference_id": 5 }
```

**Verify OTP:**
```json
{ "reference_id": 5, "otp_code": "123456" }
```

**Response:**
```json
{ "reference_id": 5, "verified": true, "verified_at": "2026-02-23T10:30:00" }
```

---

### Declaration

| Method | Endpoint | Description |
|---|---|---|
| `PUT` | `/loan/application/{id}/declaration` | Borrower confirms their financial situation and gives legal consent. |
| `GET` | `/loan/application/{id}/declaration` | Fetch the saved declaration. |

**Request:**
```json
{
  "has_existing_loans": false,
  "has_credit_card": true,
  "has_default_history": false,
  "consent_data_sharing": true,
  "agreed_terms": true,
  "consent_credit_check": true,
  "terms_version": "v1.2",
  "privacy_policy_version": "v1.0",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

---

### Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/loan/application/{id}/summary` | Full pre-submission review. Only returns `can_submit: true` when all steps are done. |

**Response (abbreviated):**
```json
{
  "application_id": 42,
  "loan_details": {
    "approved_amount": 10000,
    "interest_rate": 12,
    "emi_amount": 888.49,
    "total_repayment": 10661.88,
    "processing_fee": 500,
    "gst_on_processing_fee": 90,
    "net_disbursement_amount": 9410
  },
  "submission_status": {
    "can_submit": true,
    "pending_steps": []
  }
}
```

---

### Lender Dashboard

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/lender/applications` | See all SUBMITTED applications that no lender has claimed yet. |
| `POST` | `/lender/pick/{application_id}?lender_id={id}` | Claim an application for review. Uses a row-level lock so two lenders cannot grab the same one simultaneously. |
| `GET` | `/lender/my-applications/{lender_id}` | View all applications assigned to this lender. |
| `POST` | `/lender/approve/{application_id}?lender_id={id}` | Approve. Only the lender who picked the app can do this. |
| `POST` | `/lender/reject/{application_id}?lender_id={id}&rejection_reason=...` | Reject with a mandatory reason. |

---

### Disbursement (Admin only)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/disbursement/{application_id}` | Preview breakdown — approved amount, fees, and what the borrower will actually receive. |
| `POST` | `/admin/disbursement/{application_id}` | Send the money. Application must be in `APPROVED` status. |

**Request:**
```json
{ "payment_mode": "BANK" }
```

**Response:**
```json
{
  "id": 1,
  "application_id": 42,
  "amount": 9410.00,
  "payment_mode": "BANK",
  "payment_status": "SUCCESS",
  "payment_reference_id": "TXN20260223ABCD",
  "initiated_at": "2026-02-23T10:00:00",
  "completed_at": "2026-02-23T10:00:02"
}
```

---

## Loan Calculator Logic

All constants live in `app/services/loan_calculator.py` — fixed values, no lender-specific rates.

```python
MIN_LOAN_AMOUNT        = 5_000     # ₹5,000
MAX_LOAN_AMOUNT        = 20_000    # ₹20,000
ALLOWED_TENURES        = [3, 6, 9, 12]  # months
ANNUAL_INTEREST_RATE   = 12        # 12% per annum
PROCESSING_FEE_PERCENT = 5         # 5% of principal
GST_RATE               = 18        # 18% on processing fee only
```

### EMI Formula

```
EMI = [ P × R × (1+R)^N ] / [ (1+R)^N - 1 ]

Where:
  P = Principal (approved_amount)
  R = Monthly interest rate = 12 / 12 / 100 = 0.01
  N = Tenure in months
```

### Worked Example — ₹10,000 for 12 months

| Component | How it's calculated | Result |
|---|---|---|
| Loan amount | — | ₹10,000.00 |
| Monthly rate (R) | 12% ÷ 12 ÷ 100 | 0.01 |
| Monthly EMI | formula above | ₹888.49 |
| Total repayment | ₹888.49 × 12 | ₹10,661.88 |
| Processing fee | 5% × ₹10,000 | ₹500.00 |
| GST on fee | 18% × ₹500 | ₹90.00 |
| Total deducted upfront | ₹500 + ₹90 | ₹590.00 |
| **Borrower actually receives** | ₹10,000 − ₹590 | **₹9,410.00** |

### Credit Score Eligibility

```python
if credit_score < 650:
    status = "REJECTED"
    max_eligible_amount = 0
    failure_reason = "Credit score is below the minimum required score of 650"
else:
    status = "ELIGIBLE"
    max_eligible_amount = monthly_income × 20
```

---

## Application Status Lifecycle

```
                    ┌─────────┐
                    │  DRAFT  │  ← Created on /apply
                    └────┬────┘
                         │ Borrower submits (all steps complete)
                         ▼
                   ┌──────────┐
                   │SUBMITTED │  ← reference_number generated, app locked
                   └────┬─────┘
                         │ Lender picks it from the pool
                         ▼
                  ┌────────────┐
                  │UNDER_REVIEW│  ← lender_id assigned, lender reviewing
                  └──────┬─────┘
                         │
              ┌──────────┴───────────┐
              │ Lender approves      │ Lender rejects
              ▼                      ▼
        ┌──────────┐           ┌──────────┐
        │ APPROVED │           │ REJECTED │ ← Terminal
        └────┬─────┘           └──────────┘
             │
             │ Admin initiates disbursement
             ▼
       ┌────────────┐
       │NBFC_APPROVED│
       └──────┬──────┘
              │
              ▼
        ┌──────────┐
        │DISBURSED │  ← Net amount sent to borrower's bank/UPI
        └────┬─────┘
             │
             ▼
        ┌────────┐
        │ CLOSED │ ← Terminal
        └────────┘
```

### Step Tracker Sequence

```
LOAN_DETAILS ✓  →  PURPOSE  →  REFERENCES  →  DECLARATION  →  SUMMARY  →  SUBMITTED
   (auto-done)      Step 2       Step 3          Step 4         Step 5      Final
```

---

## Enums & Allowed Values

### `LoanApplicationStatus`

| Value | What it means |
|---|---|
| `DRAFT` | Application created, not submitted yet |
| `SUBMITTED` | Borrower submitted — sitting in the lender pool |
| `UNDER_REVIEW` | A lender has claimed it and is reviewing |
| `APPROVED` | Lender approved — ready for disbursement |
| `NBFC_APPROVED` | Approved by the NBFC partner |
| `REJECTED` | Lender rejected it — terminal, no disbursement |
| `DISBURSED` | Money sent to borrower |
| `CLOSED` | Loan fully closed — terminal |

### `LoanApplicationStep`
`LOAN_DETAILS` → `PURPOSE` → `REFERENCES` → `DECLARATION` → `SUMMARY` → `SUBMITTED`

### `LoanPurpose`
`MEDICAL` | `EDUCATION` | `EMERGENCY` | `PERSONAL`

### `ReferenceRelation`
`FRIEND` | `BROTHER` | `SISTER` | `FATHER` | `MOTHER` | `SPOUSE` | `COLLEAGUE`

### `LoanTenureMonths`
`3` | `6` | `9` | `12` *(months only — no other values accepted)*

### `DisbursementStatusEnum`
`INITIATED` | `SUCCESS` | `FAILED` | `REVERSED`

### `PaymentModeEnum`
`BANK` | `UPI`

### `EligibilityStatusEnum`
`ELIGIBLE` | `REJECTED`

---

## Error Handling

| HTTP Code | When it happens | Example |
|---|---|---|
| `400` | Credit score below 650 | `{"detail": "Credit score 580 is below the minimum required score of 650"}` |
| `400` | Loan amount out of range | `{"detail": "Requested amount exceeds eligible amount"}` |
| `400` | Application already submitted | `{"detail": "Application already submitted. Editing not allowed."}` |
| `400` | Submitting before all steps done | `{"detail": "Declaration not completed"}` |
| `400` | Lender picking an already-claimed app | `{"detail": "Already picked by another lender"}` |
| `400` | Approving/rejecting without UNDER_REVIEW status | `{"detail": "Application not in review stage"}` |
| `400` | Rejecting without a reason | `{"detail": "Rejection reason required"}` |
| `400` | Disbursing a non-APPROVED app | `{"detail": "Loan must be APPROVED before disbursement"}` |
| `400` | Already disbursed | `{"detail": "Loan already disbursed"}` |
| `400` | No verified payout method | `{"detail": "No verified BANK payout method found"}` |
| `403` | Lender acting on an app they didn't pick | `{"detail": "You did not pick this application"}` |
| `401` | Invalid/expired JWT | `{"detail": "Invalid or expired token"}` |
| `401` | User not found | `{"detail": "User not found"}` |
| `404` | Application not found | `{"detail": "Loan application not found"}` |
| `404` | Lender not found or inactive | `{"detail": "Lender not found or inactive"}` |
| `422` | Wrong field type or missing field | `{"detail": [{"loc": ["body", "field"], "msg": "...", "type": "..."}]}` |
| `500` | Step tracker missing | `{"detail": "Application step tracker missing"}` |

---

## Business Rules

```
Eligibility
  Credit score must be 650 or above to pass — anything below returns REJECTED
  No application can be started without a passing eligibility record

Loan limits
  Minimum ₹5,000  |  Maximum ₹20,000
  Tenure must be exactly 3, 6, 9, or 12 months — nothing else is accepted

Application steps
  Steps must be done in order — the step tracker enforces this
  Both references must have their OTP verified before Declaration can be submitted
  All four steps (Purpose, References, Declaration, Summary) must be complete before /submit

After submission
  Application is locked — nothing can be edited
  Reference number is generated only at this point (8-char alphanumeric)
  EMI, fees, and total repayment are calculated only at this point

Lender rules
  Only SUBMITTED apps with no lender assigned appear in the pool
  Lender must be active=True and blocked=False to pick
  Row-level DB lock (SELECT FOR UPDATE) prevents two lenders claiming the same app
  Lenders can only approve or reject apps they personally picked
  App must be in UNDER_REVIEW to approve or reject
  Rejection reason is mandatory — cannot be blank

Disbursement
  Only possible after status = APPROVED
  Borrower must have a verified bank account or UPI ID saved
  Amount sent = approved amount minus processing fee and GST (net amount only)
```

---

## Notes

- `/purpose` and `/references` use `application/x-www-form-urlencoded` (form-data), **not JSON**
- `approved_amount` comes from `loan_eligibility.max_eligible_amount` — the borrower cannot choose or override it
- `reference_number` (8-char alphanumeric) is generated only when the borrower submits
- Financial fields (`monthly_emi`, `processing_fee`, `gst_amount`, `total_repayment`) stay blank on the record until submission — the calculator fills them in at that point
- Check `submission_status.can_submit == true` in the summary before calling `/submit`
- The disbursement sends the **net** amount (after fees), not the full approved amount
- `MockNBFCPaymentGateway` simulates real transfers — replace with an actual gateway before going live

---
