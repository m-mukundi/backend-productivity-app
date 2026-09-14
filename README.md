# Backend Productivity App

A secure Flask REST API for a personal task-tracking (productivity) app. Users
register and log in with JWT-based authentication, then create, read, update,
and delete their own tasks (title, description, status). Users can never
view or modify another user's tasks.

Built for integration with the `client-with-jwt` React client from the
[Summative Lab client apps repo](https://github.com/m-mukundi/flask-c10-summative-lab-sessions-and-jwt-clients).
Route paths and JSON response shapes below match that client's `fetch` calls
exactly (`/login`, `/signup`, `/me`, `{ token, user }` responses, `{ errors:
[...] }` on failure). Run this API on port 5555; the client's
`package.json` already proxies to `http://localhost:5555`.

## Tech Stack

- Flask 2.2.2 + Flask-RESTful (resource-based routing)
- Flask-SQLAlchemy 3.0.3 + Flask-Migrate (SQLite by default)
- Flask-JWT-Extended (access tokens + server-side logout/revocation)
- Flask-Bcrypt (password hashing)
- Marshmallow (request validation/serialization)
- Faker (database seeding)

## Project Structure

```
app.py                 # App factory, route registration, JWT/error handlers
config.py               # Configuration (env-driven)
extensions.py            # Shared extension instances (db, jwt, bcrypt, migrate, cors)
schemas.py               # Marshmallow request validation schemas
models/
  user.py                # User model + password hashing
  task.py                # Task model (owned by a user)
  token_blocklist.py      # Revoked JWTs (for logout)
resources/
  auth.py                 # Signup / Login / Me / Logout
  tasks.py                 # Task CRUD + pagination, ownership checks
seed.py                  # Database seed script (Faker)
migrations/              # Flask-Migrate/Alembic migrations
```

## Installation

Requires Python 3.12+ and `pipenv`.

```bash
pipenv install --dev
```

Create a `.env` file (or copy `.env.example`) to override defaults:

```bash
cp .env.example .env
```

```
DATABASE_URL=sqlite:///app.db
JWT_SECRET_KEY=change-this-secret
SECRET_KEY=change-this-secret-too
```

### Set up the database

```bash
pipenv run flask db upgrade   # creates/updates app.db from migrations
pipenv run python seed.py     # seeds demo users + tasks
```

The seed script creates a `demo` user (`username: demo`, `password:
password123`) plus several Faker-generated users, each with a handful of
tasks in random statuses.

If you change the models, generate a new migration with:

```bash
pipenv run flask db migrate -m "describe your change"
pipenv run flask db upgrade
```

## Running the server

```bash
pipenv run flask run
```

The API runs at `http://127.0.0.1:5555` by default (configured via
`.flaskenv`). Alternatively: `pipenv run python app.py`.

## Authentication

Auth uses JSON Web Tokens via `Authorization: Bearer <token>` headers.
`POST /signup` and `POST /login` return `{ token, user }`. Every `/tasks`
route requires a valid, non-revoked token. `POST /logout` adds the token's
`jti` to a server-side blocklist so it can no longer be used. Any non-2xx
auth response returns `{ "errors": ["...", ...] }` (a flat array of message
strings).

## API Endpoints

### Auth

| Method | Endpoint  | Auth required | Description                                                                                                                                                                       |
| ------ | --------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| POST   | `/signup` | No             | Create a new user. Body: `username`, `password`, `password_confirmation`. Returns `{ token, user }`. `409` if username taken, `422` on validation errors or password mismatch. |
| POST   | `/login`  | No             | Authenticate with `username` + `password`. Returns `{ token, user }`. `401` on bad credentials.                                                                                 |
| GET    | `/me`     | Yes            | Returns the currently authenticated user (used to persist login across refreshes). `401` if token missing/invalid/expired/revoked.                                             |
| POST   | `/logout` | Yes            | Revokes the current access token so it can no longer be used.                                                                                                                   |

### Tasks (all require `Authorization: Bearer <token>`; users only ever see/act on their own tasks)

| Method | Endpoint                                   | Description                                                                                                                                                                            |
| ------ | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GET    | `/tasks?page=1&per_page=10&status=pending` | Paginated list of the current user's tasks. `status` filter is optional. Returns `tasks`, `page`, `per_page`, `total`, `total_pages`, `has_next`, `has_prev`.                          |
| POST   | `/tasks`                                   | Create a task. Body: `title` (required), `description` (optional), `status` (optional, one of `pending`/`in_progress`/`completed`, defaults to `pending`). `422` on validation errors. |
| GET    | `/tasks/<id>`                              | Fetch a single task. `404` if it doesn't exist, `403` if it belongs to another user.                                                                                                   |
| PATCH  | `/tasks/<id>`                              | Partially update a task (`title`/`description`/`status`). Same `404`/`403` ownership rules as above.                                                                                   |
| DELETE | `/tasks/<id>`                              | Delete a task. Returns `204`. Same `404`/`403` ownership rules as above.                                                                                                               |

## Deployment (Render)

This repo is ready to deploy to [Render](https://render.com) as a Blueprint:

1. Push this repo to GitHub.
2. In the Render dashboard, choose **New > Blueprint** and point it at the repo.
   Render will read [`render.yaml`](./render.yaml) and provision:
   - a free Postgres database (`backend-productivity-db`)
   - a web service that installs dependencies, runs `flask db upgrade`
     (applying migrations) on every deploy, then starts the API with
     `gunicorn app:app` (see [`Procfile`](./Procfile))
   - `DATABASE_URL` wired automatically from the database to the web
     service, plus auto-generated `JWT_SECRET_KEY`/`SECRET_KEY` values
3. After the first deploy, seed the database from your machine by running
   `pipenv run python seed.py` with `DATABASE_URL` set to the value shown
   on the Render Postgres dashboard (or open a Render shell on the web
   service and run `python seed.py` there).
4. Update the frontend client's API base URL / proxy to point at the
   Render service URL instead of `localhost:5555`.

Live URL: _add once deployed_.

Notes:
- SQLite is fine for local development but is **not** used in production —
  `render.yaml` provisions Postgres and `config.py` normalizes Render's
  `postgres://` connection string to the `postgresql://` scheme SQLAlchemy
  requires.
- `gunicorn` only runs on Linux/macOS (no Windows support), so continue
  using `pipenv run flask run` for local development on Windows.
