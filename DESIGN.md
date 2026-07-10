## Architecture overview

```
# Client (Swagger)
# FastApi (routes, Services& Models) ─▶ BackgroundTasks (export worker)─▶ exports/ folder (generated files)
# PostgreSQL

All three services (`api`, `db`, `redis`) run via Docker Compose.

## Project structure

```
app/
├── main.py           # FastAPI app instance, router registration
├── core/              # config, db session, security (hashing/JWT)
├── models/            # SQLAlchemy ORM tables 
├── schemas/           # Pydantic request/response models (wire shape, decoupled from DB shape)
├── api/
│   ├── deps.py         # get_current_user, get_db 
│   └── routes/         # thin HTTP layer: parse request, call service, response
├── services/           # business logic + authorization checks 
└── workers/             # background export worker, own DB session
```



## Data model

**users**: id (UUID pk), email (unique, indexed), hashed_password, created_at, updated_at

**lists**: id (UUID pk), owner_id (FK→users, ON DELETE CASCADE, indexed), name,
description (nullable), created_at (indexed), updated_at

**items**: id (UUID pk), list_id (FK→lists, ON DELETE CASCADE, indexed), title,
status (CHECK IN want_to_read/reading/finished), created_at (indexed), updated_at

**export_jobs**: id (UUID pk), user_id (FK→users, ON DELETE CASCADE, indexed),
list_id (FK→lists, ON DELETE CASCADE), status (CHECK IN pending/processing/completed/failed),
format (CHECK IN csv/json), file_path (nullable), error (nullable), created_at, completed_at

### Key design decisions

- **UUID primary keys**, not sequential integers — avoids leaking row counts or making
  ids guessable/enumerable.
- **ON DELETE CASCADE** on every foreign key — deleting a user automatically cleans up
  their lists, items, and export jobs; deleting a list cleans up its items and export jobs.
  No orphaned rows possible.
- **CheckConstraints** on `status`/`format` enforce valid values at the database layer,
  as a backstop to the same validation already done at the Pydantic layer
  (`Literal["want_to_read", "reading", "finished"]` etc.) — belt-and-suspenders, invalid
  values are rejected before they ever reach a query in the normal case, and the DB
  constraint guards against any future code path that might bypass the schema layer.
- **`user_id` denormalized directly onto `export_jobs`**, not only reachable via
  `list_id → lists.owner_id`. This makes the "only the owner can see their export jobs"
  check a single indexed column comparison instead of a join, and matches how the
  download endpoint needs to authorize quickly.
- **Indexes** on every column used in a WHERE or ORDER BY on a hot path: `owner_id`,
  `list_id`, `user_id`, `created_at` (used for both filtering by owner and default
  sort order on paginated collections).



## Authentication

**JWT Bearer tokens** via `Authorization: Bearer <token>` header, not cookies.

Passwords are hashed with bcrypt (via passlib) before storage, no plaintext password
persisted or returned in any response. Login failures return an identical
error message ("Invalid email or password") regardless of whether the email doesn't
exist or the password is wrong, to prevent user enumeration via differing error
messages.

Password requirements (min 8 characters, at least one digit) are enforced at the
Pydantic schema layer via a `field_validator`, returning a `422` before the request
reaches the service layer.



## Export job / async design

Export generation runs via FastAPI's in-process `BackgroundTasks`, invoked after the
`POST /lists/{list_id}/export` response (`202 Accepted`) has already been sent to the
client. The client polls `GET /exports/{job_id}` for status and calls
`GET /exports/{job_id}/download` once `status == "completed"`.



## Error handling approach


 Unauthenticated | 401 | No/invalid/expired token |
 Forbidden (not yours) | 404 | Indistinguishable from "doesn't exist" — see above |
 Invalid input | 422 | Pydantic validation, before touching the DB |
 Duplicate email | 409 | Conflict, from a DB unique constraint via `IntegrityError` |
 Export not ready for download | 409 | Conflict — job exists but isn't `completed` yet |
 Resource not found (general) | 404 | Consistent with the forbidden-access case |

## Assumptions

- Only `email` and `password` are required for registration.

## Bonus: Redis caching

Implemented for `GET /lists/{list_id}`.
