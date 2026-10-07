# Harbour OS API Contract

Backend API for the frontend team. JSON is used for request and response bodies.
The local API base is `http://localhost:5000`. Browser requests must use
`credentials: "include"` for session authentication.

## Common behavior

- Read endpoints are public. Mutation endpoints require a logged-in session
  cookie and an `Origin` matching `CORS_ORIGINS`.
- Role based access control is not implemented. A valid session is the current
  write boundary; do not treat it as harbour-manager or buyer authorization.
- API errors use `{"error":{"code":"invalid_request","message":"..."}}`.
  Common codes are `invalid_request`, `not_found`, `unauthorized`,
  `forbidden`, `conflict`, and `internal_error`. Server errors do not expose
  tracebacks.
- Auth endpoints retain their existing response shape for compatibility;
  authentication errors there use `{"error":"..."}`.
- Lists are bounded. An optional `limit` query parameter accepts a positive
  integer; values above 100 are capped at 100.
- Timestamps are ISO 8601 UTC strings ending in `Z`.
- Observations expose `source`, `confidence`, `recorded_at`,
  `freshness` (`LIVE`, `RECENT`, or `HISTORICAL`), and both
  `is_demo` and the compatibility alias `is_demo_data`. Demo observations are always classified
  `HISTORICAL`, never `LIVE`, and include a `data_label`.
- Current demo values are fictional examples, not current harbour facts.

## Health

### `GET /api/health`

**AUTH:** None  
**REQUEST:** None  
**RESPONSE:** `{"status":"ok","service":"harbour-os"}`  
**ERRORS:** Generic JSON 500 if the app cannot serve the request.  
**EXAMPLE:** `curl http://localhost:5000/api/health`

## Harbours

### `GET /api/harbours`

**AUTH:** None  
**REQUEST:** None  
**RESPONSE:** `{"harbours":[{"id":1,"name":"Munambam","district":"Ernakulam","status":"ACTIVE", ...}]}`  
**ERRORS:** None expected.  
**EXAMPLE:** `curl http://localhost:5000/api/harbours`

### `GET /api/harbours/<id>`

**AUTH:** None  
**REQUEST:** Integer path ID.  
**RESPONSE:** `{"harbour":{"id":1,"name":"Munambam","district":"Ernakulam","latitude":10.1707,"longitude":76.165,"status":"ACTIVE","created_at":"...","updated_at":"..."}}`  
**ERRORS:** 404 `not_found` if the harbour does not exist; malformed path IDs return JSON 404.  
**EXAMPLE:** `curl http://localhost:5000/api/harbours/1`

### `GET /api/harbours/<id>/dashboard`

**AUTH:** None  
**REQUEST:** Integer path ID.  
**RESPONSE:** Object with `harbour`, `recent_landings` (up to 10),
`prices` (latest per species, bounded), `active_auctions` (up to 10),
`active_buyers` (up to 20), `buyer_demand` (up to 20), `ice`,
`cold_storage`, `announcements` (up to 10), `active_alerts` (up to 10),
and `demand_attribution`.  
**ERRORS:** 404 `not_found`.  
**EXAMPLE:** `curl http://localhost:5000/api/harbours/1/dashboard`

### `GET /api/harbours/<id>/changes`

**AUTH:** None  
**REQUEST:** Integer path ID.  
**RESPONSE:** `{"harbour":{...},"events":[{"kind":"observed_event","type":"LANDING_RECORDED","observed_at":"...","summary":"...","source":"DEMO","confidence":0.9,"freshness":"HISTORICAL","is_demo_data":true,"trend":null}], "note":"..." }`  
Events are observed records/snapshots, not calculated trends. Historical
comparisons are not available in the current schema.  
**ERRORS:** 404 `not_found`.  
**EXAMPLE:** `curl http://localhost:5000/api/harbours/1/changes`

## Species

### `GET /api/species`

**AUTH:** None  
**REQUEST:** None  
**RESPONSE:** `{"species":[{"id":1,"name":"Sardine","local_name":"Mathi (മത്തി)","scientific_name":"Sardinella longiceps"}]}`  
**ERRORS:** None expected.  
**EXAMPLE:** `curl http://localhost:5000/api/species`

## Market

### `GET /api/market/prices`

**AUTH:** None  
**REQUEST:** Optional `species_id`, `harbour_id`, and `limit` query parameters.  
**RESPONSE:** `{"prices":[{"id":1,"harbour":"Kochi","species":"Sardine","value":181.0,"min_price":169.0,"max_price":190.0,"average_price":181.0,"quantity_kg":2700.0,"source":"DEMO","confidence":0.75,"recorded_at":"...","freshness":"HISTORICAL","is_demo_data":true,"data_label":"FICTIONAL PROTOTYPE DATA"}]}`  
The `value` is the average price in ₹/kg.  
**ERRORS:** 400 `invalid_request` for invalid query IDs; 404 `not_found` if a valid ID does not exist. Empty results return `{"prices":[]}`.  
**EXAMPLE:** `curl 'http://localhost:5000/api/market/prices?species_id=1&harbour_id=1'`

### `GET /api/market/compare`

**AUTH:** None  
**REQUEST:** Required `species_id` and positive `quantity_kg`; optional
`harbour_id` identifies the current harbour.  
**RESPONSE:** `{"species":{...},"quantity_kg":500,"current_harbour":{...},"demand_attribution":"...","markets":[{"harbour":{...},"price":{...},"demand":{"remaining_quantity_kg":9300.0,"source":"DEMO","confidence":0.85,"recorded_at":"...","freshness":"HISTORICAL","is_demo_data":true},"active_buyers":3,"supply":{...},"ice_available":46.0,"ice":{...},"storage_available":12.0,"storage":{...},"freshness":"HISTORICAL","is_demo_data":true}]}`  
This endpoint compares data and does not select a recommendation. Demand is
attributed by matching buyer location text to harbour name because demands
currently have no harbour foreign key.  
**ERRORS:** 400 for missing/invalid IDs or non-positive quantity; 404 if the
species or optional harbour does not exist.  
**EXAMPLE:** `curl 'http://localhost:5000/api/market/compare?species_id=1&harbour_id=1&quantity_kg=500'`

## Buyers and demand

### `GET /api/buyers`

**AUTH:** None  
**REQUEST:** Optional `harbour_id` and `limit`.  
**RESPONSE:** `{"buyers":[{"id":1,"name":"Munambam Fresh Catch","organization":"Demo buyer cooperative","location":"Munambam, Ernakulam","status":"ACTIVE","source":"DEMO","is_demo_data":true,...}]}`  
**ERRORS:** 400 invalid ID; 404 unknown harbour.  
**EXAMPLE:** `curl 'http://localhost:5000/api/buyers?harbour_id=1'`

### `GET /api/buyers/<id>`

**AUTH:** None  
**REQUEST:** Integer buyer ID.  
**RESPONSE:** `{"buyer":{"id":1,"name":"Munambam Fresh Catch",...}}`  
**ERRORS:** 404 `not_found`.  
**EXAMPLE:** `curl http://localhost:5000/api/buyers/1`

### `GET /api/buyers/<id>/demand`

**AUTH:** None  
**REQUEST:** Integer buyer ID; optional `limit`.  
**RESPONSE:** `{"buyer":{...},"demand":[{"species":"Sardine","requested_quantity_kg":3200.0,"fulfilled_quantity_kg":400.0,"remaining_quantity_kg":2800.0,"status":"PARTIAL","source":"DEMO",...}]}`  
**ERRORS:** 404 `not_found`.  
**EXAMPLE:** `curl http://localhost:5000/api/buyers/1/demand`

### `POST /api/buyers/<id>/demand`

**AUTH:** Session + allowed `Origin`.  
**REQUEST:** `{"species_id":1,"requested_quantity_kg":1200,"priority":"HIGH"}`  
**RESPONSE (201):** `{"demand":{"buyer_id":1,"species_id":1,"requested_quantity_kg":1200.0,"fulfilled_quantity_kg":0.0,"remaining_quantity_kg":1200.0,"status":"OPEN","source":"BUYER_REPORTED",...}}`  
**ERRORS:** 400 invalid body/quantity; 401 missing session; 403 origin rejected; 404 buyer/species missing.  
**EXAMPLE:** `curl -b cookies.txt -H 'Origin: http://localhost:5173' -H 'Content-Type: application/json' -d '{"species_id":1,"requested_quantity_kg":1200}' http://localhost:5000/api/buyers/1/demand`

### `PATCH /api/buyers/demand/<id>`

**AUTH:** Session + allowed `Origin`.  
**REQUEST:** Any subset of `requested_quantity_kg`, `fulfilled_quantity_kg`,
`priority`, `status`. Example: `{"fulfilled_quantity_kg":300}`.  
**RESPONSE:** `{"demand":{...,"remaining_quantity_kg":900.0,"status":"PARTIAL",...}}`  
**ERRORS:** 400 if values are invalid or fulfilled exceeds requested; 401/403
authentication/origin failures; 404 `not_found`. Remaining quantity is derived.  
**EXAMPLE:** `curl -X PATCH -b cookies.txt -H 'Origin: http://localhost:5173' -H 'Content-Type: application/json' -d '{"fulfilled_quantity_kg":300}' http://localhost:5000/api/buyers/demand/1`

## Resources

### `GET /api/resources/<harbour_id>`

**AUTH:** None  
**REQUEST:** Integer harbour ID.  
**RESPONSE:** `{"harbour":{...},"ice":{"capacity_tonnes":70.0,"available_tonnes":46.0,"price_per_kg":3.8,"queue_count":5,"status":"AVAILABLE","source":"DEMO","confidence":0.85,"recorded_at":"...","freshness":"HISTORICAL","is_demo_data":true},"cold_storage":{"capacity_tonnes":120.0,"occupied_tonnes":94.0,"reserved_tonnes":14.0,"available_tonnes":12.0,...},"is_demo_data":true}`  
**ERRORS:** 404 unknown harbour. Missing resource records are returned as `null`.  
**EXAMPLE:** `curl http://localhost:5000/api/resources/2`

### `PATCH /api/resources/<harbour_id>/ice`

**AUTH:** Session + allowed `Origin`.  
**REQUEST:** Any subset of `capacity_tonnes`, `available_tonnes`,
`price_per_kg`, `queue_count`, `status`. Example:
`{"available_tonnes":20,"queue_count":2}`.  
**RESPONSE:** `{"ice":{"available_tonnes":20.0,"source":"HARBOUR_OPERATOR","recorded_at":"...",...}}`  
**ERRORS:** 400 for negative values, invalid status, or availability above
capacity; 401/403 auth/origin; 404 if harbour/ice plant is missing.  
**EXAMPLE:** `curl -X PATCH -b cookies.txt -H 'Origin: http://localhost:5173' -H 'Content-Type: application/json' -d '{"available_tonnes":20}' http://localhost:5000/api/resources/2/ice`

### `PATCH /api/resources/<harbour_id>/storage`

**AUTH:** Session + allowed `Origin`.  
**REQUEST:** Any subset of `capacity_tonnes`, `occupied_tonnes`,
`reserved_tonnes`, `expected_release` (ISO datetime or null), `status`.  
**RESPONSE:** `{"cold_storage":{"capacity_tonnes":120.0,"occupied_tonnes":90.0,"reserved_tonnes":10.0,"available_tonnes":20.0,"source":"HARBOUR_OPERATOR",...}}`  
**ERRORS:** 400 for negative values or occupied + reserved above capacity;
401/403 auth/origin; 404 missing harbour/storage.  
**EXAMPLE:** `curl -X PATCH -b cookies.txt -H 'Origin: http://localhost:5173' -H 'Content-Type: application/json' -d '{"occupied_tonnes":90,"reserved_tonnes":10}' http://localhost:5000/api/resources/2/storage`

## Auctions

### `GET /api/auctions`

**AUTH:** None  
**REQUEST:** Optional `harbour_id`, `status`, and `limit`.  
**RESPONSE:** `{"auctions":[{"id":1,"harbour":"Kochi","species":"Sardine","quantity_kg":700.0,"starting_price":175.0,"current_price":188.0,"status":"LIVE","source":"DEMO","confidence":0.8,"recorded_at":"...",...}]}`  
**ERRORS:** 400 invalid harbour ID; 404 unknown harbour.  
**EXAMPLE:** `curl 'http://localhost:5000/api/auctions?status=LIVE&harbour_id=2'`

### `GET /api/auctions/<id>`

**AUTH:** None  
**REQUEST:** Integer auction ID.  
**RESPONSE:** `{"auction":{...,"bids":[{"buyer":{...},"amount":188.0,"timestamp":"..."}]}}` (up to 20 bids).  
**ERRORS:** 404 `not_found`.  
**EXAMPLE:** `curl http://localhost:5000/api/auctions/1`

### `POST /api/auctions`

**AUTH:** Session + allowed `Origin`.  
**REQUEST:** `{"harbour_id":2,"species_id":1,"quantity_kg":500,"starting_price":170,"quality_grade":"A"}`. Grade is optional and defaults to A. New auctions open as LIVE.  
**RESPONSE (201):** `{"auction":{...,"current_price":170.0,"status":"LIVE","source":"AUCTION_OPERATOR",...}}`  
**ERRORS:** 400 invalid values; 401/403 auth/origin; 404 harbour/species missing.  
**EXAMPLE:** `curl -b cookies.txt -H 'Origin: http://localhost:5173' -H 'Content-Type: application/json' -d '{"harbour_id":2,"species_id":1,"quantity_kg":500,"starting_price":170}' http://localhost:5000/api/auctions`

### `POST /api/auctions/<id>/bids`

**AUTH:** Session + allowed `Origin`.  
**REQUEST:** `{"buyer_id":3,"amount":181}`.  
**RESPONSE (201):** `{"auction":{...,"current_price":181.0,...},"bid":{"id":9,"buyer_id":3,"amount":181.0,"timestamp":"...","source":"AUCTION_OPERATOR","confidence":1.0,"freshness":"LIVE","is_demo":false}}`  
**ERRORS:** 400 bid must exceed current price; 401/403 auth/origin; 404
auction/buyer missing; 409 auction not LIVE or buyer inactive.  
**EXAMPLE:** `curl -b cookies.txt -H 'Origin: http://localhost:5173' -H 'Content-Type: application/json' -d '{"buyer_id":3,"amount":181}' http://localhost:5000/api/auctions/1/bids`

### `POST /api/auctions/<id>/close`

**AUTH:** Session + allowed `Origin`.  
**REQUEST:** Empty body. The highest bid wins; ties go to the earliest bid.
An auction with no bids closes without a winner.  
**RESPONSE:** `{"auction":{...,"status":"CLOSED","winner":{...}|null,"closed_at":"..."}}`  
**ERRORS:** 401/403 auth/origin; 404 missing auction; 409 if not LIVE.  
**EXAMPLE:** `curl -X POST -b cookies.txt -H 'Origin: http://localhost:5173' http://localhost:5000/api/auctions/1/close`

## Announcements and alerts

### `GET /api/announcements`

**AUTH:** None  
**REQUEST:** Optional `harbour_id` and `limit`; global announcements are
included when filtering by harbour. Expired records are omitted.  
**RESPONSE:** `{"announcements":[{"id":1,"harbour":"Kochi","title":"...","message":"...","priority":"HIGH","source":"DEMO","is_demo_data":true,...}]}`  
**ERRORS:** 400 invalid ID; 404 unknown harbour.  
**EXAMPLE:** `curl 'http://localhost:5000/api/announcements?harbour_id=2'`

### `POST /api/announcements`

**AUTH:** Session + allowed `Origin`.  
**REQUEST:** `{"harbour_id":2,"title":"Auction window","message":"Auction opens at 11:00.","priority":"HIGH","expires_at":"2026-10-08T12:00:00Z"}`. `harbour_id` and `expires_at` are optional; null harbour means general announcement.  
**RESPONSE (201):** `{"announcement":{"id":5,"title":"Auction window","source":"HARBOUR_OPERATOR","is_demo_data":false,...}}`  
**ERRORS:** 400 invalid fields/expiry; 401/403 auth/origin; 404 unknown harbour.  
**EXAMPLE:** `curl -b cookies.txt -H 'Origin: http://localhost:5173' -H 'Content-Type: application/json' -d '{"title":"Auction window","message":"Auction opens at 11:00"}' http://localhost:5000/api/announcements`

### `GET /api/alerts`

**AUTH:** None  
**REQUEST:** Optional `harbour_id`, `active=true|false` (default true), and `limit`. Expired alerts are omitted when active=true.  
**RESPONSE:** `{"alerts":[{"id":1,"harbour":"Munambam","type":"ICE_SHORTAGE","title":"...","severity":"WARNING","active":true,"source":"DEMO","is_demo_data":true,...}]}`  
**ERRORS:** 400 invalid active value/ID; 404 unknown harbour.  
**EXAMPLE:** `curl 'http://localhost:5000/api/alerts?active=true&harbour_id=1'`

### `POST /api/alerts`

**AUTH:** Session + allowed `Origin`.  
**REQUEST:** `{"harbour_id":2,"type":"AUCTION_DELAY","title":"Auction delayed","message":"Auction will begin later.","severity":"WARNING","expires_at":"2026-10-08T12:00:00Z"}`.  
**RESPONSE (201):** `{"alert":{"id":4,"harbour_id":2,"type":"AUCTION_DELAY","active":true,"source":"HARBOUR_OPERATOR","is_demo_data":false,...}}`  
**ERRORS:** 400 invalid fields/expiry; 401/403 auth/origin; 404 unknown harbour.  
**EXAMPLE:** `curl -b cookies.txt -H 'Origin: http://localhost:5173' -H 'Content-Type: application/json' -d '{"harbour_id":2,"type":"AUCTION_DELAY","title":"Auction delayed","message":"Auction will begin later"}' http://localhost:5000/api/alerts`

## Decision intelligence

### `POST /api/decision/recommend`

**AUTH:** None  
**REQUEST:** `{"species_id":1,"quantity_kg":500,"current_harbour_id":1}`. The current harbour is optional.  
**RESPONSE:** Root object with `recommendation`, `species`, `quantity_kg`,
`factors`, `reasons`, `cautions`, `data_freshness`,
`is_demo_data`, `weighting`, and `markets_considered`.  
Weights are price 0.40, demand 0.25, active buyers 0.15, resources 0.10, and
freshness 0.10. Scores are deterministic, normalized across available
harbours, and never calculated by Gemini.  
**ERRORS:** 400 invalid JSON/IDs/quantity; 404 unknown species/harbour or
`no_market_data` when there are no price observations. With missing demand,
buyers, or resources the endpoint returns a score with explicit cautions.  
**EXAMPLE:** `curl -H 'Content-Type: application/json' -d '{"species_id":1,"quantity_kg":500,"current_harbour_id":1}' http://localhost:5000/api/decision/recommend`

## AI assistant

### `POST /api/ai/assistant`

**AUTH:** None  
**REQUEST:** `{"harbour_id":1,"message":"Where should I sell 500kg sardines?"}`; message is limited to 2,000 characters.  
**RESPONSE:** Configured provider: `{"available":true,"answer":"...","context":{...}}`. Missing key: `{"available":false,"message":"AI assistant is not configured."}`. Provider failure: `{"available":false,"message":"AI assistant is temporarily unavailable.","context":{...}}`.  
Backend context includes bounded dashboard data and a deterministic
recommendation when a species and quantity are recognized. Gemini is instructed
to explain supplied facts only; it is not an authority for live facts or scores.
**ERRORS:** 400 invalid body; 404 unknown harbour. Provider failures use the
structured unavailable response, not a server error.  
**EXAMPLE:** `curl -H 'Content-Type: application/json' -d '{"harbour_id":1,"message":"Where should I sell 500kg sardines?"}' http://localhost:5000/api/ai/assistant`

## Authentication

Authentication is Flask session-cookie based. Keep the cookie jar between calls.
Frontend fetches should set `credentials: "include"`.

### `POST /api/auth/register`

**AUTH:** None  
**REQUEST:** `{"username":"demo-user","email":"demo@example.test","password":"..."}`  
**RESPONSE (201):** `{"message":"User registered successfully","user":{"id":1,"username":"demo-user","email":"demo@example.test"}}`  
**ERRORS:** 400 missing/malformed fields; 409 username/email already exists.
Auth errors preserve their legacy string `error` field.  
**EXAMPLE:** `curl -c cookies.txt -H 'Content-Type: application/json' -d '{"username":"demo-user","email":"demo@example.test","password":"password"}' http://localhost:5000/api/auth/register`

### `POST /api/auth/login`

**AUTH:** None  
**REQUEST:** `{"email":"demo@example.test","password":"..."}`  
**RESPONSE:** `{"message":"Login successful","user":{"id":1,"username":"demo-user","email":"demo@example.test"}}`; sets session cookie.  
**ERRORS:** 400 malformed fields; 401 invalid credentials.  
**EXAMPLE:** `curl -b cookies.txt -c cookies.txt -H 'Content-Type: application/json' -d '{"email":"demo@example.test","password":"password"}' http://localhost:5000/api/auth/login`

### `GET /api/auth/me`

**AUTH:** Session cookie.  
**REQUEST:** None.  
**RESPONSE:** `{"id":1,"username":"demo-user","email":"demo@example.test"}`.  
**ERRORS:** 401 `{"error":"Not authenticated"}`.  
**EXAMPLE:** `curl -b cookies.txt http://localhost:5000/api/auth/me`

### `POST /api/auth/logout`

**AUTH:** None; clears the current session cookie.  
**REQUEST:** Empty body.  
**RESPONSE:** `{"message":"Logout successful"}`.  
**ERRORS:** None expected.  
**EXAMPLE:** `curl -b cookies.txt -X POST http://localhost:5000/api/auth/logout`

## Environment and deployment

Copy `backend/.env.example` to `backend/.env` for local development.

- `SECRET_KEY`: required Flask session signing key; use a unique secret in deployment.
- `DATABASE_URL`: optional SQLAlchemy URL; defaults to the existing `sqlite:///plutii.db` database.
- `CORS_ORIGINS`: comma-separated explicit frontend origins. Defaults locally to `http://localhost:5173`. Legacy `ALLOWED_ORIGINS` is still accepted as a fallback. Wildcard origins are rejected because cookies are enabled.
- `COOKIE_SECURE`: set `true` for HTTPS deployment.
- `GEMINI_API_KEY`: optional; without it the AI endpoint reports unavailable.
- `GEMINI_MODEL`: optional; defaults to `gemini-2.0-flash`.
- `APP_ENV=production`: prevents the demo seed command from resetting operational data.

The app uses `create_all()` for new tables. It also performs a documented,
additive compatibility step for `source`, `confidence`, and
`recorded_at` on legacy auction/announcement/alert tables. Unknown legacy
provenance is marked `UNKNOWN`, not guessed; the seed marks fixture rows
`DEMO`. It does not drop tables or remove users. Future schema changes need
explicit migrations.

The root and frontend `vercel.json` rewrites still point at the old
`https://arrowlens.onrender.com` host. Set the actual backend deployment URL
when it is provisioned, then update both rewrite destinations; no production
hostname is assumed here.

## Demo seed

From the backend directory:

```bash
.venv/bin/python seed.py
```

This resets Harbour OS operational tables in dependency order and re-seeds the
deterministic Munambam/Kochi/Beypore fixture, so auction/demand/resource
mutations return to the known demo state. It never drops tables or deletes
authentication `User` rows. The reset deletes operational rows, so use it only
for the development/demo database; it refuses to run when `APP_ENV=production`.
All fixture observations use `source=DEMO`.
