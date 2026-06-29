# Expense Approval Workflow API - Implementation Plan

## Problem Statement

Organizations need a streamlined system for employees to submit expense claims and have them approved through a defined workflow. Currently, there's no standardized way to:
- Submit and track expense claims
- Route claims through appropriate approval authorities (managers and finance teams)
- Maintain an audit trail of approvals and rejections
- Enable employees to monitor the status of their submissions

## Solution

Build a FastAPI-based Expense Approval Workflow API that automates the expense claim lifecycle through three distinct roles:
1. **Employees** submit expense claims and track their status
2. **Managers** review and approve/reject employee claims
3. **Finance** processes approved claims for payment

The system maintains all claims in memory with clear state transitions and role-based access control via header-based authentication.

## User Stories

1. As an employee, I want to submit an expense claim with an amount and description, so that I can get reimbursement for my work-related expenses
2. As an employee, I want to view the status of my submitted expense claims, so that I know where they are in the approval workflow
3. As an employee, I want to view details of a specific expense claim, so that I can confirm the information was recorded correctly
4. As a manager, I want to see all pending expense claims, so that I can review and approve them in a timely manner
5. As a manager, I want to approve an expense claim with a single action, so that I can move it to the finance team for processing
6. As a manager, I want to reject an expense claim and provide a reason, so that the employee understands why their claim was not approved
7. As a finance team member, I want to view all approved expense claims, so that I can process them for payment
8. As a finance team member, I want to mark a claim as processed, so that I can track payment status
9. As an employee, I want to see rejection reasons when my claim is rejected, so that I understand what went wrong
10. As an administrator/auditor, I want to see the complete history of each expense claim, so that I can track all approvals and rejections for compliance

## Implementation Decisions

### Architecture & Framework
- **Framework**: FastAPI for modern, fast Python API development with built-in validation and auto-generated OpenAPI docs
- **Storage**: In-memory Python dictionary-based storage for simplicity (no database dependency)
- **Authentication**: Header-based mocking via `X-User-ID` and `X-User-Role` headers (no JWT/token validation)
- **User Model**: Single role per user (employee, manager, or finance) for simplicity

### Expense Claim Data Model
**Required fields:**
- `expense_id`: Unique identifier (UUID)
- `employee_id`: ID of the employee who submitted the claim
- `amount`: Positive float/decimal (must be > 0)
- `category`: Predefined category (Travel, Meals, Equipment, Other)
- `description`: Non-empty text description of the expense
- `date_submitted`: ISO 8601 timestamp of submission

**Optional fields:**
- `receipt_url`: URL or reference to receipt/documentation
- `project_code`: Internal project or cost center code for allocation
- `department`: Department for tracking

**System-managed fields:**
- `status`: One of: `SUBMITTED`, `MANAGER_PENDING`, `FINANCE_PENDING`, `APPROVED`, `REJECTED`
- `created_at`: ISO 8601 timestamp of creation
- `updated_at`: ISO 8601 timestamp of last modification
- `manager_id`: ID of the manager who approved/rejected (nullable)
- `manager_approval_reason`: Manager's comments/rejection reason (nullable)
- `finance_id`: ID of finance approver (nullable)
- `finance_approval_reason`: Finance's comments/rejection reason (nullable)

### Workflow & State Transitions
```
SUBMITTED -> MANAGER_PENDING -> FINANCE_PENDING -> APPROVED
                 |                   |
                 +-> REJECTED        +-> REJECTED
```

Rules:
- Single linear approval path: Employee submits → Manager approves/rejects → Finance approves/rejects
- Only managers can move claims from `SUBMITTED` to `MANAGER_PENDING` (on approve) or `REJECTED` (on reject)
- Only finance can move claims from `FINANCE_PENDING` to `APPROVED` or `REJECTED`
- Rejected claims are final and cannot be resubmitted; employee must create a new claim
- All state transitions must be recorded with timestamps, user IDs, and rejection reasons
- No intermediate "processed" state—`APPROVED` is the final state after finance approval

### API Endpoints & Access Control

**Employee Endpoints:**
- `POST /expenses` — Submit new expense claim (authentication: employee role required)
- `GET /expenses` — List all own expense claims (optionally filter by status)
- `GET /expenses/{expense_id}` — View specific own expense claim with full details

**Manager Endpoints:**
- `GET /expenses` — List all expense claims from direct reports (optionally filter by status)
- `PATCH /expenses/{expense_id}/approve` — Approve an expense in MANAGER_PENDING state
- `PATCH /expenses/{expense_id}/reject` — Reject an expense in MANAGER_PENDING state with reason

**Finance Endpoints:**
- `GET /expenses` — List all expense claims in FINANCE_PENDING or APPROVED state
- `PATCH /expenses/{expense_id}/approve` — Approve an expense in FINANCE_PENDING state
- `PATCH /expenses/{expense_id}/reject` — Reject an expense in FINANCE_PENDING state with reason

**Access Control Rules:**
- Managers can only see expenses from employees they manage (based on employee-manager mapping)
- Finance can see expenses that are in FINANCE_PENDING or APPROVED states
- Employees can only see their own expenses
- Employees cannot approve or reject; only managers and finance can
- Each role gets a mocked identity via `X-User-ID` and `X-User-Role` headers

### Input Validation
- **Amount:** Must be positive (> 0)
- **Category:** Must be one of: Travel, Meals, Equipment, Other
- **Description:** Must be non-empty string
- **date_submitted:** Valid ISO 8601 datetime
- **receipt_url, project_code, department:** Optional strings
- **User IDs:** Alphanumeric strings from headers (`X-User-ID` and `X-User-Role`)
- All requests must include valid `X-User-ID` and `X-User-Role` headers

### Error Handling
- **400 Bad Request:** Invalid input (negative amount, invalid category, empty description, missing required fields)
- **401 Unauthorized:** Missing or invalid authentication headers
- **403 Forbidden:** User lacks permission (e.g., employee trying to approve, manager accessing another team's expenses)
- **404 Not Found:** Expense doesn't exist or user lacks access to it
- **409 Conflict:** Invalid state transition (e.g., trying to approve already-approved expense, rejecting rejected expense)
- All errors return descriptive JSON messages for debugging

### Code Structure
```
app/
├── main.py                 # FastAPI app initialization, middleware setup
├── config.py              # Configuration constants
├── models/
│   └── expense.py        # Expense claim data models
├── database/
│   └── store.py          # In-memory storage implementation
├── routes/
│   └── expenses.py       # API endpoint handlers
├── services/
│   └── expense_service.py # Business logic & state transitions
├── auth/
│   └── middleware.py     # Header-based auth middleware
├── utils/
│   └── errors.py         # Custom exception classes
└── __init__.py

tests/
├── conftest.py          # Pytest fixtures & setup
├── test_models.py       # Unit tests for data models
├── test_service.py      # Unit tests for business logic
└── test_foundation.py   # Integration tests for API endpoints
```

### Database/Storage Layer Design
- Single in-memory dictionary keyed by claim ID
- Thread-safe operations using locks if needed
- Supports listing claims with optional status filter
- Clear separation between storage interface and implementation

## Testing Decisions

### What Makes a Good Test
- Tests external behavior (API contracts and business logic) rather than implementation details
- Tests are isolated and independent from other tests
- Tests verify both happy path and error conditions
- Tests use realistic test data and fixtures
- Tests run fast and don't depend on external systems

### Testing Strategy
- **Unit Tests**: Test individual components (models, services) in isolation
- **Integration Tests**: Test complete API workflows (submit → approve → process)
- **Fixtures**: Pre-built test data for different user roles and claim states
- **Coverage Target**: >80% code coverage
- **Test Framework**: pytest with pytest-asyncio for async endpoint testing
- **No Mocking**: Test with real in-memory storage to verify integration between layers

### Modules to Test
1. **Models** (`expense.py`): Data validation and state machine logic
2. **Services** (`expense_service.py`): Business logic and state transitions
3. **Routes** (`expenses.py`): API endpoint behavior, access control, error responses
4. **Middleware** (`middleware.py`): Authentication header parsing and validation

### Test Coverage Areas
- Creating valid and invalid expense claims
- Listing claims with role-based filtering
- Approving, rejecting, and processing claims
- State transition validation (no invalid transitions)
- Access control (employees can't approve, finance can't submit, etc.)
- Error cases (missing headers, wrong role, nonexistent claims)
- Rejection reason capture and retrieval

## Out of Scope

- **Persistent Storage**: Database integration is out of scope; in-memory storage only
- **Real Authentication**: JWT tokens, OAuth, or credential validation
- **Authorization Levels**: No approval thresholds (e.g., auto-approve under $X)
- **Business Logic Rules**: No expense categories, department codes, or cost center tracking
- **Attachments/Receipts**: No file upload or receipt storage
- **Notifications**: No email or push notifications for approvals/rejections
- **Audit Logging**: No detailed audit trail beyond timestamps and user IDs
- **Pagination**: List endpoints return all results (acceptable for in-memory storage)
- **Search/Filtering**: Only basic status filtering; no advanced query capabilities
- **Multi-tenant**: Single-organization system only
- **Performance Optimization**: No caching, no query optimization needed for in-memory storage

## Key Assumptions & Constraints

1. **Single-process deployment**: In-memory storage works only for single-process apps; not suitable for distributed systems
2. **Data loss on restart**: All expenses are lost when the application restarts
3. **No concurrent modifications**: Assumes low concurrency; no optimistic locking needed for MVP
4. **Simple user model**: Users have a single immutable role (employee, manager, finance); no role hierarchy
5. **Synchronous operations**: All operations complete immediately; no async workflows
6. **Small dataset**: In-memory storage works for hundreds/thousands of expenses; not millions
7. **Fixed employee-manager mapping**: Managers are statically associated with their direct reports (configured at startup or via fixtures)
8. **No resubmission support**: Rejected expenses cannot be resubmitted; new submission required
9. **Linear approval path**: Expenses always follow the same sequence; no approval thresholds or alternate paths

## Further Notes

- This plan follows production-quality code standards: clear separation of concerns, comprehensive error handling, and full test coverage
- The architecture is designed to be easily testable and maintainable
- If persistence is needed in the future, the storage layer can be swapped out without changing service or route logic
- The header-based auth is suitable for development/testing; real deployments should use proper authentication schemes
- Consider adding request logging/tracing middleware for production observability
