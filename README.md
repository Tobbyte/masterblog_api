# Masterblog

A small Flask blog with file-based storage. It started as a purely server-side rendered app (create, update, delete and like posts) and was extended with a RESTful JSON API. For that, the original `Masterblog` class was split into a shared base class and two subclasses:

- **`MasterblogSSR`**: the original server-side rendered frontend (HTML forms and templates).
- **`MasterblogApi`**: a RESTful API with search, sorting, pagination, rate limiting, CORS and Swagger documentation. A minimal client-side rendered page is included for debugging only.

## Features

- Create, read, update, delete and like posts
- Likes are tied to a session cookie (one like per visitor and post, toggleable), not to a login
- REST API with sorting, pagination and search by title and/or content
- Strict validation of all query parameters, with error messages that name the offending parameter
- Rate limiting (100 requests per minute per IP) and CORS support
- Interactive API documentation via Swagger UI
- JSON error responses in the API (400, 404, 405, 429, 500), HTML error pages in the SSR frontend
- Health check before every request: if the JSON storage is corrupted, the app responds with a 500 instead of failing mid-request

## Requirements
- Python 3.10+
- Werkzeug, Flask, Flask-CORS, Flask-Limiter and Flask_Swagger_Ui (see `requirements.txt`)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the commands from the directory that contains the `masterblog_api/` package.

**API** (port 5002):

```bash
python -m masterblog_api.backend.backend_app
```

- API base: `http://127.0.0.1:5002/api/posts`
- Swagger UI: `http://127.0.0.1:5002/api/docs/`

**Server-side rendered frontend** (port 5001):

```bash
python -m masterblog_api.frontend.frontend_app_ssr
```

Open `http://127.0.0.1:5001` in your browser.

**Client-side debug frontend** (port 5001, requires the running API):

```bash
python -m masterblog_api.frontend.frontend_app_csr
```

The SSR and CSR frontends use the same port, so only run one of them at a time.

## Project structure

| File | Purpose |
| --- | --- |
| `masterblog_app.py` | `Masterblog` base class: Flask setup, DB health check, session user ID, post ID handling, add/delete/update/like logic |
| `blog_store.py` | `BlogStore` class for JSON persistence |
| `config.py` | Shared constants, file paths and error messages |
| `backend/backend_app.py` | `MasterblogApi`: API routes, query parameter validation, search, sorting, pagination, JSON error handlers, `InvalidParamError` |
| `backend/backend_config.py` | API constants (parameter names, allowed parameters per endpoint, allowed values, defaults, error messages) |
| `backend/swagger.py` | Swagger UI setup |
| `frontend/frontend_app_ssr.py` | `MasterblogSSR`: server-side rendered routes and HTML error pages |
| `frontend/frontend_app_csr.py` | Minimal client-side debug page for the API |
| `frontend/templates/` | HTML templates |

A post looks like this:

```json
{
  "id": 1,
  "author": "Tobi",
  "title": "Hello",
  "content": "First post",
  "liked_by": ["<user uid>"]
}
```

## API

Full interactive documentation is available at `/api/docs/`. Overview:

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/posts` | List posts (sorting and pagination) |
| `POST` | `/api/posts` | Create a post |
| `PUT` | `/api/posts/<id>` | Update title and/or content |
| `DELETE` | `/api/posts/<id>` | Delete a post |
| `POST` | `/api/posts/<id>/like` | Toggle the current visitor's like |
| `GET` | `/api/posts/search` | Search posts by title and/or content |

### Query parameters for sorting and pagination

Used by `GET /api/posts` and `GET /api/posts/search`:

| Parameter | Description |
| --- | --- |
| `sort` | Optional: `id`, `title` or `content` |
| `direction` | Optional: `asc` (default) or `desc`. Only used together with `sort`, otherwise ignored. |
| `page` | Whole number, at least 1 (default: first page) |
| `per_page` | Whole number, at least 1 and at most the configured maximum (`API_PAGINATION_MAX_PAGE_SIZE` in `backend_config.py`) |

Ties in sorting are broken by `id`.

### Strict parameter validation

Query parameters are validated before anything else happens, and the rules are strict:

- **Unknown parameters are rejected**, and so are parameters that belong to another endpoint (for example `title` on `GET /api/posts`).
- **Values with a fixed set of options must match exactly**: lowercase, no surrounding whitespace (`desc`, not `DESC` or ` desc`).
- **Numbers must be whole numbers within range.** Search terms must not be empty.

Any violation returns `400` with a JSON message that names the parameter, for example:

```json
{ "error": "Invalid value for 'direction'"}
```

The response format for list and search:

```json
{
  "posts": [],
  "page": 1,
  "per_page": 10,
  "total": 0,
  "total_pages": 0
}
```

### Create a post: `POST /api/posts`

JSON body with `title`, `content` and `author`. All three are required, non-empty strings. Returns the new post with its ID and status `201`. Invalid data returns `400`.

### Update a post: `PUT /api/posts/<id>`

JSON body with string values. Only `title` and `content` can be changed; empty values and all other fields are ignored. The body itself must be a non-empty JSON object, otherwise `400`. A body without a usable `title` or `content` changes nothing and still returns `200` with the post's current values. Returns `id`, `title` and `content`, or `404` if the post does not exist.

Note: the semantics are those of a partial update (PATCH), but the route uses `PUT` as the exercise required.

### Delete a post: `DELETE /api/posts/<id>`

Returns a confirmation message (`200`) or `404`.

### Like a post: `POST /api/posts/<id>/like`

Toggles the like of the current session. Returns `id`, `liked` (the current state) and `like_count`, or `404`.

### Search: `GET /api/posts/search`

| Parameter | Description |
| --- | --- |
| `title` | Search term in the title |
| `content` | Search term in the content |
| `match_either` | `true`: title **or** content must match. `false` (default): both must match. Irrelevant if only one term is given. |
| `sort`, `direction`, `page`, `per_page` | Sorting and pagination as described above, applied to the search results |

Matching is a case-insensitive substring search, and surrounding whitespace in the search term is ignored. At least one of `title` or `content` is required and must not be empty, otherwise `400`. The response has the same format as the post list.

## Known limitations

This project was built for an assignment that focuses on the API. These issues are known and were deliberately not fixed for this submission:

- **No validation in the SSR frontend.** `add` and `update` pass the submitted form data on without checking it. Empty posts are possible, and a manipulated form can store arbitrary fields, including `liked_by`, which can later cause a 500 error. Validation and field whitelisting should move into the base class so both frontends share it (the API already does this).
- **All `liked_by` user IDs are exposed** in the API responses for post lists.
- **Wide-open CORS with credentials.** Any origin is accepted. This is dangerous and should be restricted to the known frontend origin.
- **Race conditions.** The Flask development server is multithreaded, and every write rewrites the whole JSON file and the ID file. Concurrent requests can produce duplicate IDs or lost updates. A lock or a real database (e.g. SQLite) would fix this.
- **No authentication.** Anyone can edit or delete any post. Likes are tracked per session cookie, with a hardcoded mock "secret" key.
- **Request bodies expect all fields as strings.** Wrongly typed or unneeded fields in the JSON body lead to a `400`.
- **No automated tests and no logging yet.**
- **`sys.path` hacks** in the entry-point modules. A proper package setup (e.g. `pyproject.toml` with an editable install) would remove them.

## Possible next steps

- Inject `BlogStore` as a dependency instead of creating it in the base class (also makes testing easier)
- Replace the `KeyError` for "post not found" with a custom exception and a central error handler
- Move validation, search, sorting and pagination into functions that don't depend on Flask, so they can be unit tested
- Split the base class further (application setup vs. post logic)
- Cache data in the DB health check instead of reloading on every request
- Add tests and logging

## Acknowledgement

- Made with ❤️ and without ai or code completion (except this readme, for code-reviews or where otherwise explicitly stated (swagger json, js, html)).