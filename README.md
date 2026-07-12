# Reading List API

A Personal Catalog API where each user owns Lists, each Shelf contains Books
(Items), and any Shelf can be exported to a background-generated CSV/JSON file.

Built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker Compose and Redis.

## Tech stack

- Python 3.11+, FastAPI
- PostgreSQL 16 — primary data store
- SQLAlchemy 2.0 (ORM) + Alembic (migrations)
- Redis 7 — used for caching single-resource list reads 
- JWT authentication (python-jose + passlib/bcrypt)
- pytest — automated tests
- Docker + Docker Compose
- Strawberry GraphQL

## Prerequisites

- Docker Desktop (with Docker Compose)
- Python/Postgres/Redis all run inside containers, no local installs required
  to run the API itself. (A local Python venv is only needed if you want to run the
  automated test suite from the host — see "Running tests" below.)

## Setup and run


1. Clone the repository:
```bash
   git clone https://github.com/noor-ridha/Reading-list-with-FastApi
   cd reading-list-api
```

2. Copy the environment template:
```bash
   cp .env.example .env
```
   Default values work out of the box for local development. Change `SECRET_KEY` to
   a random string for anything beyond local testing.

3. Start the full stack:
```bash
   docker compose up --build
```
   This builds the API image, starts PostgreSQL and Redis, waits for Postgres to pass
   its healthcheck, runs database migrations automatically, and starts the API on
   port 8000. No separate migration step is needed.

4. Open the interactive API docs:
   ```
   http://localhost:8000/docs
   ```

6. Health check:
   ```
   GET http://localhost:8000/health
   → {"status": "ok"}
   ```

To stop everything:
```bash
docker compose down
```

To reset the database completely (drops all data):
```bash
docker compose down -v
```

## Environment variables

See `.env.example` for the full list with placeholder values. Summary:

| Variable | Purpose |
|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Database credentials |
| `DATABASE_URL` | Full SQLAlchemy connection string (note: the `api` container overrides the host to `db` via `docker-compose.yml`; `.env`'s value uses `localhost` for host-side tools like Alembic run outside Docker) |
| `REDIS_URL` | Redis connection string (provisioned, not yet used by app code) |
| `SECRET_KEY` | JWT signing secret — change for any non-local use |
| `ALGORITHM` | JWT signing algorithm (HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token lifetime |

## Authentication

Bearer token via `Authorization: Bearer <token>` header — not cookies (this is an
API-only service;

### Register
```
POST /auth/register
Content-Type: application/json

{
  "email": "you@example.com",
  "password": "yourpassword1"
}
```
Password must be at least 8 characters and contain at least one digit.

Returns `201` with the created user (never includes the password/hash).
Returns `409` if the email is already registered.
Returns `422` if the password doesn't meet the strength requirement or the email
is malformed.

### Login
```
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=you@example.com&password=yourpassword1
```
(Note: `username` field carries the email — this is standard OAuth2 password flow
form shape, which is also what Swagger's "Authorize" button uses automatically.)

Returns `200` with `{"access_token": "...", "token_type": "bearer"}`.
Returns `401` for invalid credentials.

Use the token on all subsequent requests: `Authorization: Bearer <access_token>`.

## API reference

All endpoints below except `/health`, `/auth/register`, and `/auth/login` require a
valid Bearer token.

### Lists

| Method | Path | Description |
|---|---|---|
| POST | `/lists` | Create a list |
| GET | `/lists?limit=20&offset=0` | Paginated list of your lists |
| GET | `/lists/{list_id}` | Get one list |
| PATCH | `/lists/{list_id}` | Update a list |
| DELETE | `/lists/{list_id}` | Delete a list |

### Items

| Method | Path | Description |
|---|---|---|
| POST | `/lists/{list_id}/items` | Add an item to a list |
| GET | `/lists/{list_id}/items?limit=20&offset=0` | Paginated items in a list |
| GET | `/lists/{list_id}/items/{item_id}` | Get one item |
| PATCH | `/lists/{list_id}/items/{item_id}` | Update an item |
| DELETE | `/lists/{list_id}/items/{item_id}` | Delete an item |

Item `status` accepts: `want_to_read`, `reading`, `finished`.

### Export

| Method | Path | Description |
|---|---|---|
| POST | `/lists/{list_id}/export` | Kick off a background export (`format`: `csv` or `json`) |
| GET | `/exports/{job_id}` | Check export job status |
| GET | `/exports/{job_id}/download` | Download the completed export file |

Export job `status` values: `pending` → `processing` → `completed` / `failed`.
Downloading before `completed` returns `409`.

### Example: full flow with curl

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"test1234"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -d "username=you@example.com&password=test1234"
# → copy the access_token from the response

# Create a list
curl -X POST http://localhost:8000/lists \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Sci-Fi Favorites"}'

# Add an item
curl -X POST http://localhost:8000/lists/<list_id>/items \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Dune","status":"reading"}'

# Export the list
curl -X POST http://localhost:8000/lists/<list_id>/export \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"format":"json"}'

# Check status / download
curl http://localhost:8000/exports/<job_id> -H "Authorization: Bearer <token>"
curl http://localhost:8000/exports/<job_id>/download -H "Authorization: Bearer <token>" -o export.json
```

## Running tests

Tests run against a separate test database

1. Create the test database (once):
   ```bash
   docker exec -it reading_list_db psql -U reading_list_user -d postgres -c "CREATE DATABASE reading_list_test_db;"
   ```

2. Ensure `TEST_DATABASE_URL` is set in `.env` (see `.env.example`).

3. Create and activate a virtual environment, then install dependencies:
```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\Activate.ps1
   # macOS/Linux
   source .venv/bin/activate

   pip install -r requirements.txt
```

4. Run the tests:
```bash
   pytest -v
```
Test coverage includes: registration/login, cross-user authorization isolation,
invalid input / duplicate-email constraint handling, and the full export job
lifecycle — plus additional cases beyond the required minimum of 4.

## Known limitations

- - **Export jobs run in-process** via FastAPI `BackgroundTasks`. If the server process
  crashes or restarts while a job is `processing`, that job is permanently stuck and
  will not be retried automatically.
- **No password reset / change flow** — out of scope for this assessment; only
  register and login are implemented.
- **No token revocation / logout** — JWTs are stateless; discarding the token
  client-side is the only "logout" mechanism.
- **Redis caching only covers single-list reads** (`GET /lists/{list_id}`) — item-level
  caching and collection-endpoint caching were scoped but not implemented due to time
  constraints. See DESIGN.md for the reasoning.

## Bonus: Caching (Redis)

`GET /lists/{list_id}` is cached in Redis, keyed by `list:{owner_id}:{list_id}`, with
delete-on-write invalidation on update/delete and a 300-second TTL as a safety net.


To observe it directly:
```bash
docker exec -it reading_list_redis redis-cli KEYS "list:*"
docker exec -it reading_list_redis redis-cli GET "list:<owner_id>:<list_id>"
```

## Bonus: GraphQL

A limited GraphQL interface is available at `http://localhost:8000/graphql`, alongside
the full REST API. It intentionally covers a smaller, read-oriented surface — REST
remains the complete interface.

**Available operations:**
- `myLists(limit, offset)` — paginated list of your lists
- `list(id)` — a single list with its items nested in one request
- `exportJob(id)` — export job status
- `createList(name, description)` — mutation
- `addItem(listId, title, status)` — mutation

**Auth:** same Bearer token as REST, passed via an `Authorization: Bearer <token>`
header in the GraphQL request (set this in GraphiQL's "Headers" panel when testing
interactively at `/graphql`).

**Example query** (fetches a list and its items in a single round trip, unlike REST
which needs two calls for the same data):
```graphql

query {
  list(id: "your-list-id") {
    name
    items {
      title
      status
    }
  }
}
```

**Example mutation:**
```graphql
mutation {
  createList(name: "Sci-Fi Favorites") {
    id
    name
  }
}
```


## AI Tools Used

Claude Opus + Sonnet 5: Co-thinking, enhancing project structure, enhancing the code and the documatations.
