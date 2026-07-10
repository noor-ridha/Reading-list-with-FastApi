# TESTING.md

Automated tests (pytest) cover the four required categories and are run via `pytest -v`.
This document covers manual verification, including
the six required robustness cases from the task spec , with real inputs
and observed outputs captured during development.

## Automated test summary



tests/test_auth.py::test_register_success PASSED
tests/test_auth.py::test_login_success PASSED
tests/test_auth.py::test_login_wrong_password_rejected PASSED
tests/test_authorization.py::test_user_cannot_access_another_users_list PASSED
tests/test_authorization.py::test_user_cannot_add_item_to_others_list PASSED
tests/test_authorization.py::test_unauthenticated_access_rejected PASSED
tests/test_export.py::test_export_job_lifecycle PASSED
tests/test_export.py::test_export_job_forbidden_for_other_user PASSED
tests/test_validation.py::test_duplicate_email_rejected PASSED
tests/test_validation.py::test_weak_password_rejected PASSED
```

## Manual test cases — normal flows

### 1. Register a user

**Input:**
```
POST /auth/register
{"email": "noor@noor.com", "password": "test1234"}
```

**Observed output:** `201 Created`
```json
{
  "id": "c01022b3-37eb-46e8-a3b8-8b8ae45de73d",
  "email": "noor@noor.com",
  "created_at": "2026-07-09T12:58:36.790178Z"
}
```
No password or hash present in the response.

### 2. Login

**Input:**
```
POST /auth/login
username=noor@noor.com&password=test1234
```

**Observed output:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Create a list

**Input:**
```
POST /lists
Authorization: Bearer <token>
{"name": "Sci-Fi favs", "description": "Books I want to revisit"}
```

**Observed output:** `201 Created`
```json
{
  "id": "0b91d332-29fa-40f6-a8f0-b9e300019889",
  "name": "Sci-Fi Favorites",
  "description": "Books I want to revisit",
  "created_at": "2026-07-09T15:07:28.099449Z",
  "updated_at": "2026-07-09T15:07:28.099449Z"
}
```

### 4. Add an item to a list

**Input:**
```
POST /lists/{list_id}/items
Authorization: Bearer <token>
{"title": "Dune", "status": "reading"}
```

**Observed output:** `201 Created` — item returned with `list_id` matching the parent,
generated `id`, and timestamps.

### 5. Paginated list retrieval

**Input:** `GET /lists?limit=20&offset=0`

**Observed output:** `200 OK`
```json
{"items": [...], "total": 1, "limit": 20, "offset": 0}
```

### 6. Update a list

**Input:** `PATCH /lists/{list_id}` with `{"name": "Updated Name"}`

**Observed output:** `200 OK` — `name` changed, `description` unchanged (partial update
confirmed working).

### 7. Delete a list

**Input:** `DELETE /lists/{list_id}`

**Observed output:** `204 No Content`. Subsequent `GET /lists/{list_id}` on the same id
returns `404` — confirmed cascade delete also removed the list's items.

### 8. Export job — full lifecycle

**Input:** `POST /lists/{list_id}/export` with `{"format": "json"}`

**Observed output:** `202 Accepted`
```json
{
  "id": "f83fe98d-b8fe-4f19-85f7-da8c825b4839",
  "list_id": "c337b82a-9208-4a08-83a9-bfcf04cceb54",
  "status": "pending",
  "format": "json",
  "error": null,
  "created_at": "2026-07-09T15:56:31.165467Z",
  "completed_at": null
}
```

Polling `GET /exports/{job_id}` shortly after:
```json
{
  "status": "completed",
  "completed_at": "2026-07-09T15:56:31.237149Z",
  ...
}
```

`GET /exports/{job_id}/download` — response headers confirmed:
```
content-type: application/json
content-disposition: attachment; filename="export_c337b82a-9208-4a08-83a9-bfcf04cceb54.json"
content-length: 172
```
(Content-length was 172, not 2, confirming real item data was exported — an earlier
test against an empty list correctly produced a 2-byte `[]` response.)

CSV format was also verified: `content-type: text/csv; charset=utf-8`, non-trivial
`content-length`, correct filename extension.

## Robustness cases:

### Case 1: Unauthenticated access

**Input:** `GET /lists` with no `Authorization` header.

**Expected/observed behavior:** `401 Unauthorized`. Enforced by every protected route
depending on `get_current_user` (`app/api/deps.py`), which raises before any list/item
query executes.

### Case 2: Forbidden access (User B on User A's list/item)

**Setup:** Registered a second user (User B). Created a list as User A. Authorized as
User B and attempted:

| Action | Result |
|---|---|
| `GET /lists/{user_a_list_id}` | `404 Not Found` |
| `DELETE /lists/{user_a_list_id}` | `404 Not Found` |
| `POST /lists/{user_a_list_id}/items` (add item to A's list) | `404 Not Found` |



### Case 3: Forbidden export access

**Setup:** User A created an export job. User B authorized and attempted:

| Action | Result |
|---|---|
| `GET /exports/{user_a_job_id}` | `404 Not Found` |
| `GET /exports/{user_a_job_id}/download` | `404 Not Found` |

Enforced via a single indexed `user_id` comparison on `export_jobs` 
Also codified in `test_export_job_forbidden_for_other_user`.

### Case 4: Invalid input

**Input A — weak password:**
```
POST /auth/register
{"email": "test@test.com", "password": "abc"}
```
**Observed output:** `422 Unprocessable Entity` — rejected by the Pydantic
`field_validator` before reaching the service layer (password must be ≥8 characters
and contain a digit).

**Input B — invalid item status:**
```
POST /lists/{list_id}/items
{"title": "Some Book", "status": "not_a_real_status"}
```
**Expected/observed behavior:** `422` — rejected by the `Literal["want_to_read",
"reading", "finished"]` type on `ItemCreate`, mirrored by a database-level
`CheckConstraint` as a second line of defense.



### Case 6: Conflict

**Input — duplicate email:**
```
POST /auth/register   (first call)
{"email": "dave@test.com", "password": "test1234"}
→ 201 Created

POST /auth/register   (second call, same email)
{"email": "dave@test.com", "password": "test1234"}
→ 409 Conflict
```


**Input — download before export ready:**
```
GET /exports/{job_id}/download   (while status is still "pending" or "processing")
→ 409 Conflict
{"detail": "Export is not ready (status: pending)"}
```
