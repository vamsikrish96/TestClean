# Expense Approval Workflow API - Implementation Plan

## Problem Statement

Organizations need a streamlined process for employees to submit expense claims and for managers/finance teams to review, approve, and process those claims. Currently, manual tracking via email or spreadsheets creates bottlenecks, loss of accountability, and limited visibility into claim status.

## Solution

Build a production-quality FastAPI-based REST API that:
- Allows employees to submit expense claims with required details (amount, category, description, expense date, receipt URL)
- Enables managers to approve/reject claims from their team members
- Allows finance to process approved claims
- Provides employees with complete visibility into their claims' status and full approval workflow history
- Maintains a complete audit trail of all state transitions with timestamps, approvers, and rejection reasons
- Supports enterprise scale (1000+ employees) with role-based access control (employee, manager, finance)

## Requirements

### Functional Requirements

#### Expense Submission (Employee)
1. Employee submits a new expense with required fields:
   - Amount (0 < amount ≤ $100,000)
   - Category (Travel, Meals, Equipment, Other)
   - Description (text)
   - Expense Date (≤ today)
   - Receipt URL (mandatory)
2. System validates all inputs and returns validation errors if invalid
3. Expense starts in "pending" status, waiting for manager approval
4. Employee can only see their own submitted expenses

#### Expense Viewing (Employee)
1. Employee can list their own expenses with filtering by status
2. Employee can view detail of a single expense including:
   - Current expense data
   - Complete audit trail showing each approval step (who, when, action, any comments)
3. If rejected, employee sees the rejection reason

#### Expense Approval (Manager)
1. Manager can list expenses pending approval from their direct reports
2. Manager can list all expenses (with various status filters) from their team
3. Manager can approve an expense (transitions to "approved_by_manager")
4. Manager can reject an expense with a mandatory rejection reason
5. Manager can only approve/reject expenses from their direct reports

#### Expense Processing (Finance)
1. Finance can list all expenses in "approved_by_manager" status
2. Finance can view expense details with full audit trail
3. Finance can approve an expense (transitions to "approved_by_finance")
4. Finance can reject an expense with a mandatory rejection reason (returns to awaiting manager review or terminal rejected)
5. Finance can mark an expense as "processed" (final state)

#### Audit Trail
1. Every status transition is recorded with:
   - From status
   - To status
   - Who made the change (user_id)
   - When the change occurred (timestamp)
   - Comment/rejection reason (mandatory if rejecting)
2. Full audit trail is visible to employee who submitted the claim

### Non-Functional Requirements
1. Production-quality code following clean code principles
2. Comprehensive unit and integration tests with 80%+ coverage
3. Input validation on all endpoints
4. Mocked authentication (no real JWT signing, but token format validated)
5. In-memory data storage (no external database)
6. Modular architecture: auth, services, and data layers as separate concerns
7. Enterprise scale support (1000+ employees)

## Architectural Decisions

### Authentication & Authorization
**Decision**: Use Bearer token authentication with embedded user_id and role (mocked JWT format).

**Rationale**: Allows testing without real JWT infrastructure while maintaining realistic token-based auth pattern. Simpler than session-based auth for stateless API.

**Implementation**:
- Authorization header format: `Authorization: Bearer <user_id>:<role>`
- Supported roles: `employee`, `manager`, `finance`
- Middleware extracts user from header on every request
- Returns 401 if header missing, 403 if role lacks permission
- No real JWT signing; tokens are validated structurally

### Workflow State Machine
**Decision**: Three-stage linear workflow: Employee → Manager → Finance

**Rationale**: Matches typical organizational approval hierarchies; simple enough to implement v1 but realistic for enterprise use.

**States**:
- `pending` — waiting for manager approval
- `approved_by_manager` — manager approved, awaiting finance review
- `approved_by_finance` — finance approved, ready for processing/payout
- `rejected` — rejected by manager or finance (terminal state)
- `processed` — finance marked as processed (terminal state)

**Transitions**:
- Employee submits → `pending`
- Manager approves → `approved_by_manager`
- Manager rejects → `rejected` (with mandatory reason)
- Finance approves → `approved_by_finance`
- Finance rejects → `rejected` (with mandatory reason)
- Finance processes → `processed`

### Data Model
**Decision**: Separate Expense and ExpenseHistory records for current state and full audit trail.

**Rationale**: Enables efficient queries for current expenses while maintaining complete, immutable audit trail.

**Expense Entity**:
- `id` (UUID)
- `employee_id` (who submitted)
- `amount` (decimal, validated: 0 < amount ≤ 100,000)
- `category` (enum: Travel, Meals, Equipment, Other)
- `description` (string)
- `expense_date` (date, ≤ today)
- `receipt_url` (string, mandatory)
- `status` (current state)
- `created_at` (timestamp)
- `updated_at` (timestamp)
- `approved_by` (user_id of approver, nullable)
- `rejection_reason` (string, nullable, required if rejected)

**ExpenseHistory Entity**:
- `id` (UUID)
- `expense_id` (reference to Expense)
- `status_from` (previous status)
- `status_to` (new status)
- `changed_by` (who made the change)
- `changed_at` (timestamp)
- `comment` (rejection reason or approver note)

### Modular Architecture
**Decision**: Organize code into distinct modules: auth, services, repositories, schemas, models, and API routes.

**Rationale**: Enables independent testing, clear separation of concerns, and easier long-term maintenance and scaling.

**Module Structure**:
```
app/
├── models/           # Data models (Expense, ExpenseHistory, User)
├── schemas/          # Pydantic request/response schemas
├── auth/             # Authentication middleware, JWT parsing
├── repositories/     # Data access layer (in-memory storage)
├── services/         # Business logic (ExpenseService, ApprovalService)
├── api/              # Route handlers and endpoint definitions
└── main.py           # FastAPI app initialization and startup
```

### In-Memory Storage
**Decision**: Use Python dicts/lists for data persistence (no external database).

**Rationale**: Simpler to test and deploy; acceptable for MVP/validation; scales to enterprise scale via efficient indexing.

**Implementation**:
- Expense repository uses dict keyed by expense_id
- ExpenseHistory repository uses dict with lists of history records per expense_id
- User repository stores employee-manager relationships and role mappings
- All data is lost on application restart (acceptable for this MVP)

## API Endpoints

### Employee Endpoints
- `POST /expenses` — Submit a new expense (requires employee role)
- `GET /expenses` — List own expenses with optional status filter (requires employee role)
- `GET /expenses/{id}` — View expense detail with full audit trail (requires employee role)

### Manager Endpoints
- `GET /expenses/team` — List expenses from direct reports with optional status filter
- `GET /expenses/team/{employee_id}` — List specific employee's expenses
- `PATCH /expenses/{id}/approve` — Approve an expense (requires manager role, must be own report)
- `PATCH /expenses/{id}/reject` — Reject an expense with reason (requires manager role, must be own report)

### Finance Endpoints
- `GET /expenses` — List all expenses with optional status filter (requires finance role)
- `GET /expenses/{id}` — View expense detail with full audit trail (requires finance role)
- `PATCH /expenses/{id}/approve` — Approve an expense (requires finance role)
- `PATCH /expenses/{id}/reject` — Reject an expense with reason (requires finance role)
- `PATCH /expenses/{id}/process` — Mark expense as processed (requires finance role)

### Request/Response Contracts
All endpoints return consistent response structure:
- 200/201 for success with response body
- 400 for validation errors with field-level error details
- 401 for missing/invalid auth header
- 403 for insufficient permissions
- 404 for not found resources

## Testing Strategy

### Good Test Characteristics
- Test external behavior, not implementation details
- Test at the highest seam possible (API endpoints > services > repositories)
- One assertion per test focused on a single behavior
- Clear, descriptive test names that explain the scenario and expected outcome
- Isolated from other tests (no shared state)

### Test Coverage Plan

#### Unit Tests
- **Services layer**: Test business logic in isolation (ExpenseService, ApprovalService)
  - Valid and invalid inputs
  - State transitions
  - Validation rules
  - Authorization checks
- **Repositories layer**: Test data access patterns
  - Create/read/update/list operations
  - Filtering and indexing
- **Schemas layer**: Test input validation
  - Valid and invalid Pydantic schemas

#### Integration Tests
- **Complete workflows**: Test full approval chain
  - Employee submits → Manager approves → Finance processes
  - Employee submits → Manager rejects (with reason)
  - Finance rejects approved claim (with reason)
  - Full audit trail recorded correctly
- **Role-based access**: Test authorization
  - Employee cannot approve/reject
  - Manager can only approve own reports
  - Finance can only approve/process approved claims

#### API Tests (Endpoint Contract Tests)
- **Endpoint behavior**: Test HTTP contracts
  - POST /expenses with valid/invalid data
  - GET /expenses with various status filters
  - PATCH /expenses/{id}/approve/reject with proper response codes
  - 401/403 responses for auth failures
  - 400 responses for validation failures
- **Happy path workflows**: End-to-end API sequences
  - Submit → Approve → Process
  - Submit → Reject with reason

### Test Organization
- Mirror app structure: `tests/services/`, `tests/repositories/`, `tests/api/`
- Fixtures for common test data (users, expenses in various states)
- Mock implementations for simple dependencies (e.g., in-memory user repository for role testing)

### Coverage Target
- 80%+ coverage on business logic (services, repositories, schemas)
- All public API endpoints tested with happy and sad paths
- All role-based access scenarios tested

## Feature Slices

The implementation will be broken into vertical slices, each delivering end-to-end functionality:

1. **Foundation Setup** - Models, in-memory repositories, auth middleware
2. **Employee Expense Submission** - POST /expenses with validation
3. **Employee View Expenses** - GET /expenses endpoints
4. **Employee View Expense Detail** - GET /expenses/{id} with audit trail
5. **Manager Approval Workflow** - Manager approve/reject endpoints
6. **Finance Processing Workflow** - Finance approve/reject/process endpoints
7. **Admin Access & Testing** - Test utilities and access patterns

Each slice includes:
- Data model changes (if needed)
- API endpoint implementation
- Business logic/services
- Input validation
- Unit and integration tests
- Audit trail updates

## Out of Scope

The following are explicitly out of scope for this implementation:

1. **Real JWT signing/verification** — Using mocked Bearer tokens
2. **External authentication providers** — No OAuth, SAML, or identity server integration
3. **Database persistence** — In-memory storage only; data lost on restart
4. **File storage for receipts** — Storing receipt URLs as strings; no file upload/download
5. **Email notifications** — No automatic emails to employees/managers on status changes
6. **Delegation of approvals** — Managers cannot delegate approval to others
7. **Expense editing after submission** — Claims are locked once submitted
8. **Category or amount limits** — No per-category spending caps or monthly limits
9. **Audit log export/reporting** — No reports or bulk audit log downloads
10. **API documentation UI** — No Swagger/OpenAPI UI (but contracts documented in code)
11. **Pagination and sorting advanced options** — Basic offset/limit only
12. **Attachment upload** — Receipt URLs only, no file uploads

## Key Assumptions

1. Users are pre-configured in the system with their role and manager relationships
2. No real user authentication; mocked via Bearer token header for testing
3. One manager per employee (no matrix reporting)
4. Managers can approve expenses for direct reports; Finance can approve from any manager
5. Rejection is terminal; no resubmission workflow in v1
6. All timestamps are in UTC
7. All amounts are in USD (no multi-currency support)
8. Expense dates cannot be future-dated

## Implementation Notes

- Follow clean code principles throughout (single responsibility, DRY, meaningful names)
- Use type hints on all functions
- Comprehensive docstrings for public APIs and non-obvious logic
- Error messages are user-friendly and actionable
- All endpoints are stateless (FastAPI dependency injection for auth)
- Request/response contracts are consistent and versioned in comments
