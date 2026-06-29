# Expense Approval Workflow API — Implementation Plan

**Date:** 2026-06-29  
**Status:** Ready for Implementation  
**Slicing Strategy:** Vertical feature slices with independent, testable workflows

---

## Problem Statement

Organizations need a streamlined expense approval workflow where:
- Employees can submit expense claims without manual intervention
- Managers can review and approve/reject claims for their team members
- Finance can process approved claims for reimbursement
- All parties can track the status and audit history of expenses
- The system enforces role-based access control and validation rules

Current state: Slices 1-4 have implemented the foundation (FastAPI setup, auth middleware, employee submission, and expense viewing). Remaining: Manager approval, Finance processing, and audit trail integration.

---

## Solution

Extend the existing FastAPI-based Expense Approval Workflow API with two new feature slices:

**Slice 5: Manager Approval Workflow**
- Managers can view pending expenses from their direct reports only
- Managers can approve or reject expenses with optional notes
- Rejected expenses require full resubmission (not editable)
- Audit trail captures approver, timestamp, and notes

**Slice 6: Finance Processing Workflow**
- Finance can view all approved expenses awaiting processing
- Finance can mark expenses as processed (completed) or return to manager (for re-review)
- Processing captures timestamp and optional notes
- Finance users have system-wide visibility

---

## User Stories

1. As an **employee**, I want to submit an expense with amount, description, and optional receipt reference, so that I can request reimbursement.

2. As an **employee**, I want to view all my submitted expenses with their current status (SUBMITTED, APPROVED, REJECTED, PROCESSED), so that I can track my reimbursements.

3. As an **employee**, I want to see who approved/rejected my expense and when, so that I can understand the workflow progress.

4. As an **employee**, I want to resubmit a new expense if my previous one was rejected, so that I can address the manager's concerns.

5. As an **employee**, I want validation to prevent me from submitting invalid expenses (negative amounts, missing descriptions, future dates), so that I don't waste manager time on malformed requests.

6. As a **manager**, I want to view all pending (SUBMITTED) expenses from my direct reports, so that I can approve them efficiently.

7. As a **manager**, I want to approve an expense with optional notes, so that I can move it forward in the workflow.

8. As a **manager**, I want to reject an expense with required notes, so that I can give the employee feedback on why it was rejected.

9. As a **manager**, I want to ensure I cannot accidentally approve my own expense, so that there's no self-approval loophole.

10. As a **manager**, I want to be prevented from modifying an expense that has already been approved/rejected, so that the workflow cannot be reversed accidentally.

11. As a **finance user**, I want to view all approved expenses awaiting processing, so that I can process them for payment.

12. As a **finance user**, I want to mark an expense as processed after verification, so that it's marked complete for accounting purposes.

13. As a **finance user**, I want to return an approved expense to the manager (not the employee) if there's a compliance issue, so that the manager can re-review it.

14. As a **finance user**, I want to add notes when processing or returning an expense, so that there's a record of why the action was taken.

15. As a **finance user**, I want system-wide visibility across all expenses regardless of employee/manager, so that I can process all approved claims.

16. As an **admin**, I want to view all expenses across all employees and statuses, so that I can audit the entire workflow.

17. As any **system user**, I want the audit trail to show who took each action (approve, reject, process, return) with timestamps and notes, so that the workflow is fully traceable.

18. As a **system administrator**, I want rejected expenses to require full resubmission (not editable), so that there's no ambiguity about which version is being reviewed.

19. As a **developer maintaining the system**, I want comprehensive tests covering happy paths, sad paths, and corner cases (concurrent updates, self-approval attempts, role violations), so that the workflow is reliable in production.

20. As a **developer**, I want role-based access control enforced at every endpoint, so that employees cannot view manager/finance endpoints and vice versa.

## Implementation Decisions

### 1. **Expense State Machine & Workflow**
- **States:** SUBMITTED → APPROVED or REJECTED → (if APPROVED) → PROCESSED or RETURNED
- **Rejected expenses:** Require full resubmission (no editing of rejected expense)
- **Returned expenses:** Sent back to Manager (not Employee) for re-review from APPROVED state
- **Rationale:** Clean state transitions prevent ambiguity; requiring resubmission on rejection ensures clear intent

### 2. **Role-Based Access Control**
- **Employees:** Can submit expenses and view their own expenses only
- **Managers:** Can view/approve/reject ONLY expenses from direct reports (enforced by manager_id relationship on Employee records)
- **Finance:** Can view all APPROVED expenses and process/return them; visibility is system-wide
- **Admin:** Can view all expenses regardless of status or employee
- **Self-approval prevention:** Any user attempting to approve their own expense receives HTTP 403 Forbidden
- **Rationale:** Multi-tenancy (managers see only their team) reduces risk of accidental approvals; self-approval check ensures compliance

### 3. **Audit Trail & Approver Tracking**
- **Timestamp fields:** `submitted_date`, `approval_date`, `processing_date`, `returned_date` (if applicable)
- **Approver identity:** Store `approved_by` (Manager user_id) and `processed_by` (Finance user_id) on Expense record
- **Notes fields:** `manager_notes` (on approval/rejection), `finance_notes` (on processing/return)
- **Rationale:** Full traceability required for compliance and dispute resolution

### 4. **Validation Rules**
- **Amount:** Positive, max $100,000 per expense
- **Description:** Required, non-empty, max 500 characters
- **Expense date:** Must not be in the future (validates expense_date field if included)
- **Rejection notes:** Required field (min 1 character, max 500) when rejecting
- **Approval/Processing notes:** Optional (max 500 characters)
- **Rationale:** Prevents invalid states early; required rejection notes ensure managers provide feedback

### 5. **Data Model Extensions**
- Add to **Expense model:**
  - `expense_date: datetime` — when the expense occurred (defaults to submitted_date if omitted)
  - `approved_by: Optional[str]` — Manager user_id who approved
  - `processed_by: Optional[str]` — Finance user_id who processed
  - `returned_date: Optional[datetime]` — timestamp when Finance returned to Manager
  - `category: Optional[str]` — (optional field; enum of Travel, Meals, Equipment, Other)

- Add to **Employee record** (if implementing manager relationships):
  - `manager_id: Optional[str]` — User ID of the employee's manager
  - **Note:** For MVP, may use mock data; actual implementation would link to HR system

- Add to **ExpenseStore:**
  - `list_by_manager(manager_id)` — returns SUBMITTED expenses for that manager's team
  - `list_by_status(status)` — already exists; used for manager/finance queries
  - `list_by_approved()` — returns all APPROVED expenses (for Finance)

### 6. **API Endpoint Design**

**Employee Endpoints** (require `employee` role):
- `POST /expenses` — Submit expense (already implemented in Slice 4)
- `GET /expenses` — List own expenses (already implemented in Slice 4)
- `GET /expenses/{expense_id}` — View own expense detail (already implemented in Slice 4)

**Manager Endpoints** (require `manager` role):
- `GET /expenses/pending` — List SUBMITTED expenses from own team (already stubbed in Slice 4)
- `PUT /expenses/{expense_id}/approve` — Approve expense (already implemented in Slice 4)
- `PUT /expenses/{expense_id}/reject` — Reject expense (already implemented in Slice 4)

**Finance Endpoints** (require `finance` role):
- `GET /expenses/approved` — List all APPROVED expenses awaiting processing (NEW — Slice 6)
- `PUT /expenses/{expense_id}/process` — Mark as PROCESSED (NEW — Slice 6)
- `PUT /expenses/{expense_id}/return` — Return to manager from APPROVED state (NEW — Slice 6)

**Admin Endpoints** (require `admin` role):
- `GET /expenses/all` — List all expenses across all statuses/employees (NEW — Slice 6)

### 7. **Mocked Authentication**
- Use Base64-encoded Bearer tokens with JSON payload: `{"user_id": "...", "role": "..."}`
- No real JWT/signing; authentication is mocked for testing purposes
- Tokens include `user_id` and `role`; may add `manager_id` for team filtering
- **Example:** `Bearer eyJ1c2VyX2lkIjogImVtcF8xMjMiLCAicm9sZSI6ICJlbXBsb3llZSJ9`

### 8. **Concurrent Update Handling**
- **Approach:** Optimistic locking via version number
- Add `version: int` field to Expense model (incremented on each update)
- On update, check that provided version matches stored version; return 409 Conflict if mismatch
- **Rationale:** In-memory storage is single-threaded in FastAPI by default, but versioning prevents accidental overwrites in high-concurrency scenarios

### 9. **Error Handling & Status Codes**
- `400 Bad Request` — Validation failure (invalid amount, missing description, future date, etc.)
- `401 Unauthorized` — Missing/invalid token
- `403 Forbidden` — Insufficient role, self-approval attempt, accessing another employee's expense
- `404 Not Found` — Expense does not exist
- `409 Conflict` — Version mismatch (concurrent update detected)
- `422 Unprocessable Entity` — Invalid state transition (e.g., trying to approve already-approved expense)
- **Rationale:** Clear error codes allow clients to handle retry/user feedback appropriately

### 10. **In-Memory Storage & Scope**
- Use dictionary-based store (already implemented in ExpenseStore)
- Data is lost on server restart (acceptable for MVP/testing)
- For production, migrate to persistent DB (PostgreSQL recommended; minimal code changes needed)
- **Rationale:** Fast iteration, no external dependencies, clear boundary between business logic and persistence

## Testing Decisions

### What Makes a Good Test
- **Test external behavior, not implementation details:** Assert on API responses and database state, not internal variable assignments
- **One assertion per test where possible:** Clearer failure messages; exception: multi-step state assertions (e.g., approve → verify status changed)
- **Avoid brittle mocks:** Use real in-memory store; mock only external dependencies (auth tokens)
- **Test both success and failure paths:** Happy path + sad paths (validation, access control, state violations)
- **Corner cases must be covered:** Self-approval, concurrent updates, role crossing, invalid state transitions

### Test Coverage by Module

**Models & Validation** (test_models.py — existing)
- Valid expense submission with all required fields
- Invalid expense: negative amount, zero amount, amount exceeds $100,000
- Invalid expense: empty description, description > 500 chars
- Invalid rejection: missing manager_notes
- Invalid approval: manager_notes too long (> 500 chars)

**Database/Store** (test_database.py — existing)
- Create, read, update, delete operations
- List by employee, list by status
- Update existing vs. non-existent expense
- **NEW:** List by manager (manager's team only)
- **NEW:** Concurrent update detection (version mismatch)

**Authentication & Authorization** (test_auth.py — existing)
- Valid token decoding
- Invalid/missing token rejection
- Role-based access control (employee ≠ manager ≠ finance)
- **NEW:** Manager cannot approve own expense
- **NEW:** Finance cannot approve (manager-only action)

**Employee Workflow** (test_submit_expense.py, test_view_expenses.py — existing)
- Submit valid expense → stored with SUBMITTED status
- Submit invalid expense → 400 Bad Request
- View own expenses → returns only own expenses
- View another employee's expense → 403 Forbidden
- **NEW:** Resubmit after rejection → creates new expense

**Manager Approval Workflow** (NEW — Slice 5)
- Manager views pending expenses → only their team's expenses
- Manager approves expense → status changes to APPROVED, approval_date set, approved_by captured
- Manager rejects expense → status changes to REJECTED, manager_notes required
- Manager cannot approve own expense → 403 Forbidden
- Manager cannot approve already-approved expense → 422 Unprocessable Entity
- Manager cannot approve rejected expense → 422 Unprocessable Entity
- Rejection notes are captured and returned in expense detail
- Approval notes (optional) are captured

**Finance Processing Workflow** (NEW — Slice 6)
- Finance views approved expenses → returns only APPROVED expenses
- Finance processes expense → status changes to PROCESSED, processing_date set, processed_by captured
- Finance returns expense to manager → status changes back to APPROVED, returned_date set, finance_notes captured
- Finance cannot process non-approved expense → 422 Unprocessable Entity
- Finance cannot process already-processed expense → 422 Unprocessable Entity
- Finance sees system-wide expenses (not limited to team)
- Employee cannot view finance-only endpoints → 403 Forbidden
- Manager cannot view finance-only endpoints → 403 Forbidden

**Admin Workflow** (NEW — Slice 6)
- Admin views all expenses → returns all regardless of status/employee
- Non-admin cannot access /expenses/all → 403 Forbidden

**Corner Cases & Edge Cases**
- Concurrent approval attempts on same expense → version mismatch prevents double-approval
- Employee tries to approve another's expense → 403 Forbidden
- Manager with no direct reports → list_pending returns empty
- Expense with minimum valid data (amount, description only) → accepted
- Expense with maximum valid amounts (amount=$100k, description=500 chars) → accepted
- Manager tries to return expense (Finance-only) → 403 Forbidden
- Finance user cannot reject (Manager-only) → 403 Forbidden
- Updated expense shows all audit fields (approved_by, processing_date, etc.)

### Test Seams
- **Single seam:** Use the existing FastAPI dependency injection to mock auth tokens in tests
- **No new seams required:** Existing store, models, and route structure support all test scenarios
- Tests instantiate store and app directly; use test client to invoke routes with mock tokens

---

## Out of Scope

1. **Persistent Database:** This plan uses in-memory storage; production migration to PostgreSQL/etc. is deferred
2. **Real JWT Authentication:** Using Base64-encoded mock tokens; cryptographic signing deferred
3. **Manager-Employee Relationships:** Manager filtering uses mock `manager_id`; real HR system integration deferred
4. **Expense Categories/Rules:** Categories are optional; category-specific validation (e.g., "Meals ≤ $50") deferred
5. **Receipt Upload/Attachment:** Receipt references are text-only; file upload deferred
6. **Notifications:** No email/Slack notifications when expenses are approved/rejected
7. **Scheduled Processing:** No batch processing or scheduled reimbursement runs
8. **Reporting/Analytics:** No dashboards, aggregate reports, or trend analysis
9. **Tax/Accounting Integration:** No export to QuickBooks or accounting systems
10. **Multi-Currency Support:** All amounts in a single currency (USD assumed)
11. **Approval Workflows with Escalation:** No multi-level approval chains or escalation rules
12. **Expense Amendments:** Cannot edit submitted expenses; must reject and resubmit
13. **Bulk Operations:** No bulk approve/reject endpoints

---

## Further Notes

### Implementation Order (Feature Slices)
1. **Slice 5: Manager Approval Workflow**
   - Endpoints: `GET /expenses/pending`, `PUT /expenses/{id}/approve`, `PUT /expenses/{id}/reject`
   - Model updates: `approved_by` field, `manager_notes` field
   - Store updates: `list_by_manager()` method
   - Tests: Manager approval, rejection, access control, corner cases

2. **Slice 6: Finance Processing & Admin Access**
   - Endpoints: `GET /expenses/approved`, `PUT /expenses/{id}/process`, `PUT /expenses/{id}/return`, `GET /expenses/all`
   - Model updates: `processed_by`, `returned_date`, `finance_notes` fields
   - Store updates: `list_by_approved()` method, filter logic
   - Tests: Finance processing, return, admin access, end-to-end workflows

### Assumptions
- Single FastAPI application; no microservices
- In-memory storage persists for the lifetime of the process only
- Employees know their manager_id for auth token claims (or hardcoded in test data)
- No concurrent requests requiring distributed locking (in-memory store is sufficient)
- All timestamps in UTC

### Key Design Principles
- **Clear state machine:** Expenses move through predictable states; no ambiguous transitions
- **Audit-first:** Every action is recorded with who, when, and why
- **Role separation:** Each role has distinct responsibilities; no cross-role actions
- **Fail-safe defaults:** Require explicit approval; no auto-approval; rejection requires notes
- **Test-driven:** Comprehensive tests ensure reliability before hand-off to QA

---

**Next Step:** Invoke `/to-issues` to break this plan into finalized feature slices ready for implementation.
