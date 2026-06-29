# Expense Approval Workflow API - Implementation Plan

## Problem Statement

Organizations need a streamlined way to manage employee expense claims from submission through approval to processing. Currently, expense workflows are manual and lack transparency:
- Employees don't know the status of their submitted expenses
- Managers have no centralized way to review and approve/reject claims
- Finance teams lack visibility into which expenses are ready to process
- There's no audit trail of the approval workflow

## Solution

Build a RESTful Expense Approval Workflow API using Python and FastAPI that automates the three-stage approval process:
1. **Submission**: Employees submit expense claims with details
2. **Review**: Managers approve or reject claims with feedback
3. **Processing**: Finance processes approved claims

The system provides:
- Role-based access control (Employee, Manager, Finance)
- Simple mock authentication using JWT-like tokens
- In-memory data storage for quick iteration
- Comprehensive input validation
- Full audit trail of status changes with timestamps and notes
- RESTful endpoints for each role's workflow

## User Stories

1. As an employee, I want to submit an expense claim with amount and description, so that I can get reimbursed for business expenses
2. As an employee, I want to view the status of my submitted expense, so that I know where it is in the approval workflow
3. As an employee, I want to list all my expenses, so that I can track my submission history
4. As a manager, I want to see all pending (SUBMITTED) expenses from my team, so that I can review and approve them
5. As a manager, I want to approve a submitted expense with optional notes, so that I can allow it to proceed to finance processing
6. As a manager, I want to reject a submitted expense with feedback notes, so that I can inform the employee why it wasn't approved
7. As finance staff, I want to see all approved expenses awaiting processing, so that I can prioritize my work
8. As finance staff, I want to mark an approved expense as processed with notes, so that I can complete the workflow
9. As a system, I want to validate all expense submissions, so that only valid data enters the system
10. As a system, I want to enforce role-based access control, so that employees can't approve expenses or finance can't submit them
11. As a system, I want to maintain an audit trail with timestamps for each workflow stage, so that there's visibility into when actions occurred
12. As a developer, I want comprehensive unit tests, so that I can refactor with confidence

## Implementation Decisions

### 1. Workflow Architecture
- **Linear three-stage approval**: Employee submit → Manager approval → Finance processing
- **Terminal states**: REJECTED by manager or PROCESSED by finance are final
- **No draft stage**: Expenses go directly from submission to SUBMITTED state (no draft persistence)
- **No edit/cancel**: Simplify initial version; can add later

### 2. Expense Data Model
Each expense tracks:
- `id`: UUID or sequential identifier
- `employee_id`: ID of employee who submitted
- `amount`: Expense amount (positive decimal)
- `description`: What the expense was for (text)
- `status`: Current workflow state (SUBMITTED, APPROVED, REJECTED, PROCESSED)
- `submitted_date`: ISO timestamp when created
- `approval_date`: ISO timestamp when manager approved (null if not approved)
- `processing_date`: ISO timestamp when finance processed (null if not processed)
- `manager_notes`: Optional feedback from manager on approval/rejection
- `finance_notes`: Optional notes from finance during processing

### 3. Expense Status Transitions
```
SUBMITTED --[manager approves]--> APPROVED --[finance processes]--> PROCESSED
SUBMITTED --[manager rejects]--> REJECTED (terminal)
```

### 4. Authentication & Authorization Strategy
- **Token format**: JWT-like base64-encoded JSON payload with `user_id` and `role`
  - Example payload: `{"user_id": "emp_123", "role": "employee"}`
  - Example token: `Authorization: Bearer eyJ1c2VyX2lkIjogImVtcF8xMjMiLCAicm9sZSI6ICJlbXBsb3llZSJ9`
- **Token validation**: Strict - reject requests without valid token
- **Roles**: `employee`, `manager`, `finance`
- **Role-based endpoint access**: Each endpoint only accessible to specific role(s)
- **Self-identification**: Employee can only view/submit their own expenses (via employee_id match in request body)

### 5. API Endpoints & Contracts

#### Employee Endpoints
- `POST /expenses` - Submit new expense
  - Request: `{amount, description}` (employee_id from token)
  - Response: Full expense object with id and status=SUBMITTED
  - Auth: employee role only
  
- `GET /expenses/{id}` - View specific expense
  - Response: Full expense object
  - Auth: employee role, self-owned expenses only
  
- `GET /expenses` - List own expenses
  - Query params: `?status=SUBMITTED&limit=50&offset=0` (optional filters)
  - Response: List of expense objects
  - Auth: employee role, filtered to own expenses

#### Manager Endpoints
- `GET /expenses/pending` - List all SUBMITTED expenses awaiting approval
  - Query params: `?limit=50&offset=0`
  - Response: List of SUBMITTED expenses
  - Auth: manager role only
  
- `PUT /expenses/{id}/approve` - Approve an expense
  - Request: `{manager_notes?}` (optional notes)
  - Response: Updated expense object with status=APPROVED
  - Auth: manager role only
  
- `PUT /expenses/{id}/reject` - Reject an expense
  - Request: `{manager_notes}` (required - tell employee why)
  - Response: Updated expense object with status=REJECTED
  - Auth: manager role only

#### Finance Endpoints
- `GET /expenses/approved` - List all APPROVED expenses awaiting processing
  - Query params: `?limit=50&offset=0`
  - Response: List of APPROVED expenses
  - Auth: finance role only
  
- `PUT /expenses/{id}/process` - Mark expense as processed
  - Request: `{finance_notes?}` (optional processing notes)
  - Response: Updated expense object with status=PROCESSED
  - Auth: finance role only

### 6. Input Validation Rules
- `amount`: Required, must be positive number, max $100,000
- `description`: Required, non-empty, 1-500 characters
- `employee_id`: Must match authenticated user's ID in token
- `manager_notes` (on reject): Required, 1-500 characters
- `manager_notes` (on approve): Optional, 0-500 characters
- `finance_notes`: Optional, 0-500 characters
- All state transitions must be valid (can't approve an already-rejected expense, etc.)

### 7. Data Storage
- **In-memory dictionary/list storage** for all expenses
- **No persistence to disk/database** (as specified)
- **Expense lookup**: By ID for fast retrieval
- **Filtering**: In-memory filtering for listing by status, employee_id, etc.

### 8. Code Organization
- `app/` - Main application package
  - `main.py` - FastAPI app setup, middleware, routes mounting
  - `models/` - Pydantic models for Expense, API requests/responses
  - `routes/` - Endpoint handlers organized by feature (expenses, health checks)
  - `services/` - Business logic (expense workflow state transitions)
  - `database/` - In-memory store abstraction
  - `auth/` - Token decoding and role validation middleware
  - `utils/` - Error handling, validation helpers
- `tests/` - Test suite
  - `conftest.py` - Pytest fixtures for test client, auth tokens
  - `test_auth.py` - Authentication and authorization tests
  - `test_models.py` - Pydantic model validation tests
  - `test_store.py` - In-memory storage tests
  - `test_submit_expense.py` - End-to-end workflow tests
  - Additional test files for manager and finance workflows

### 9. Testing Approach
- **Scope**: Unit and integration tests, NO mocking of core business logic
- **Auth tokens**: Use test fixtures to generate valid tokens for each role
- **Test data**: Use in-memory store directly in tests
- **Coverage areas**:
  - Authentication/authorization (valid/invalid tokens, role restrictions)
  - Expense submission validation and creation
  - Workflow state transitions (approve, reject, process)
  - Self-owned expense access
  - List filtering (by status, employee)
  - Error cases (invalid amounts, missing fields, unauthorized access)
- **Test seam**: High-level integration tests via FastAPI test client (no mocking of auth or services)

## Testing Decisions

### What Makes a Good Test
- Tests external behavior (API responses, status codes) rather than implementation details
- Tests run against real in-memory storage (not mocked)
- Tests verify both happy path and error scenarios
- Tests are independent and can run in any order
- Tests have clear, descriptive names

### Modules to Test
1. **Authentication**: Token decoding, role extraction, middleware enforcement
2. **Expense Models**: Pydantic validation for submit/approve/reject/process payloads
3. **In-memory Store**: CRUD operations, filtering by status/employee
4. **Expense Service**: State transition logic (can approve SUBMITTED? can process APPROVED?)
5. **API Endpoints**: All 7 endpoints with valid/invalid inputs, role restrictions
6. **Workflow Integration**: End-to-end flows (submit → approve → process, submit → reject)

### Prior Art
- Test client fixture via `TestClient(app)`
- Parametrized tests for multiple scenarios (different roles, different statuses)
- Fixtures for test tokens and test expenses
- Assert response status codes and JSON structure

## Out of Scope

- **Real authentication/JWT signing**: Token is simple base64-encoded JSON
- **Database persistence**: All data lost on app restart
- **Receipt uploads/file handling**: Expense has no receipt field
- **Delegation/forwarding**: Manager can't delegate approval to another manager
- **Expense categories**: All expenses treated equally
- **Amount thresholds**: No different approval rules based on expense amount
- **Audit logging to external system**: Timestamps tracked in-memory only
- **Email notifications**: No notifications to employees/managers on state changes
- **Reporting/analytics**: No dashboard or reporting endpoints
- **Edit/cancel expenses**: Once submitted, can't be modified or cancelled
- **Concurrent approval handling**: No locking (not required for in-memory store)
- **Pagination sorting**: Basic offset/limit only, no sort parameters

## Further Notes

### Future Enhancements (Not in Scope)
1. Add expense categories and category-based routing rules
2. Add approval amount thresholds (e.g., > $5,000 requires multiple approvers)
3. Integrate with real database (PostgreSQL, MongoDB, etc.)
4. Add real JWT authentication with signing keys
5. Add email notifications at each workflow stage
6. Add expense edit/cancel capabilities
7. Add admin dashboard with reporting and analytics
8. Add file uploads for receipt images/PDFs
9. Add expense attachment metadata
10. Add comment threads for reviewer questions

### Production Readiness Checklist
- [x] Input validation on all endpoints
- [x] Role-based access control
- [x] Clear error messages
- [x] Comprehensive unit tests
- [x] Audit trail with timestamps
- [x] Code organized into logical layers
- [x] No hardcoded secrets (mock auth uses no secrets)
- [ ] Logging/monitoring (can add later)
- [ ] Rate limiting (can add later)
- [ ] CORS configuration (can add later)
- [ ] API documentation/OpenAPI (can add later)

### Dependencies
```
fastapi==0.104.x
uvicorn==0.24.x
pydantic==2.x
pytest==7.x
httpx==0.25.x (for test client)
python-multipart (if form data needed)
```

---

**Status**: Ready for implementation via feature slices  
**Last Updated**: 2026-06-29
