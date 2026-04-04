# Portfolio Tracker — Build Progress

This document tracks every step of the build in small, reviewable chunks.
Each step produces something you can test before moving to the next one.

---

## How to read this

- Each phase has a goal — what it unlocks
- Each step is a small unit of work (1–4 files max)
- After each step there is a checkpoint — what you can test to confirm it worked
- Status markers: ✅ done · 🔄 in progress · ⬜ not started

---

## Phase 1 — Infrastructure ✅

Goal: stack runs, app starts, health endpoint returns 200.

| Step | What we built | Files |
|------|--------------|-------|
| ✅ 1.1 | Project skeleton, dependencies, Docker setup | `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example` |
| ✅ 1.2 | Typed config loaded from environment variables | `app/config.py` |
| ✅ 1.3 | Structured logging (pretty in dev, JSON in prod) | `app/core/logging.py` |
| ✅ 1.4 | Domain exceptions wired to HTTP error responses | `app/core/exceptions.py` |
| ✅ 1.5 | SQLAlchemy base class and timestamp mixin | `app/models/base.py` |
| ✅ 1.6 | Redis connection pool | `app/cache/client.py` |
| ✅ 1.7 | Database session factory and FastAPI dependency | `app/dependencies.py` |
| ✅ 1.8 | Health endpoint — checks DB + Redis | `app/api/health.py` |
| ✅ 1.9 | App factory with startup/shutdown lifecycle | `app/main.py` |
| ✅ 1.10 | Alembic wired to async SQLAlchemy | `alembic.ini`, `migrations/env.py` |

**Phase 1 checkpoint:** `curl http://localhost:8001/health` → `{"status":"ok","db":"ok","redis":"ok"}`

---

## Phase 2 — Auth ⬜

Goal: users can register and log in. All future endpoints are protected by JWT.

| Step | What we build | Files |
|------|--------------|-------|
| ⬜ 2.1 | User ORM model | `app/models/user.py` |
| ⬜ 2.2 | First Alembic migration — creates users table | `migrations/versions/001_users.py` |
| ⬜ 2.3 | Password hashing + JWT encode/decode utilities | `app/core/security.py` |
| ⬜ 2.4 | User repository — DB queries for user lookup/create | `app/repositories/user_repo.py` |
| ⬜ 2.5 | Auth service — register and login logic | `app/domain/auth/service.py`, `app/domain/auth/schemas.py` |
| ⬜ 2.6 | Auth routes — POST /auth/register, POST /auth/login | `app/api/v1/auth.py` |
| ⬜ 2.7 | get_current_user dependency — validates JWT on protected routes | `app/dependencies.py` (updated) |
| ⬜ 2.8 | Wire auth router into the app | `app/api/v1/router.py`, `app/main.py` (updated) |

**Phase 2 checkpoint:**
- `POST /api/v1/auth/register` creates a user
- `POST /api/v1/auth/login` returns a JWT
- `GET /api/v1/portfolios` with no token returns 401

---

## Phase 3 — Portfolio + Position CRUD ⬜

Goal: authenticated users can create portfolios and add positions to them.

| Step | What we build | Files |
|------|--------------|-------|
| ⬜ 3.1 | Portfolio + Position ORM models | `app/models/portfolio.py`, `app/models/position.py` |
| ⬜ 3.2 | Migration — creates portfolios + positions tables | `migrations/versions/002_portfolios_positions.py` |
| ⬜ 3.3 | Portfolio repository — CRUD queries | `app/repositories/portfolio_repo.py` |
| ⬜ 3.4 | Position repository — CRUD queries | `app/repositories/position_repo.py` |
| ⬜ 3.5 | Portfolio service — business logic for create/read/update/delete | `app/domain/portfolio/service.py`, `app/domain/portfolio/schemas.py` |
| ⬜ 3.6 | Position service — add/update/remove a position | `app/domain/position/service.py`, `app/domain/position/schemas.py` |
| ⬜ 3.7 | Portfolio API routes — CRUD endpoints | `app/api/v1/portfolios.py` |
| ⬜ 3.8 | Position API routes — CRUD endpoints under a portfolio | `app/api/v1/positions.py` |

**Phase 3 checkpoint:**
- Create a portfolio: `POST /api/v1/portfolios`
- Add AAPL position: `POST /api/v1/portfolios/{id}/positions`
- List positions: `GET /api/v1/portfolios/{id}/positions`
- Another user cannot see your portfolio (ownership check)

---

## Phase 4 — Market Data + Price Ingestor ⬜

Goal: a background task fetches mock prices and writes them to Redis every N seconds.

| Step | What we build | Files |
|------|--------------|-------|
| ⬜ 4.1 | MarketDataProvider abstract base class | `app/market_data/base.py` |
| ⬜ 4.2 | MockProvider — fake prices with small realistic drift | `app/market_data/mock_provider.py` |
| ⬜ 4.3 | Price cache — read/write latest price in Redis | `app/cache/price_cache.py` |
| ⬜ 4.4 | Price ingestor — asyncio loop: fetch → compare → cache → publish | `app/market_data/ingestor.py` |
| ⬜ 4.5 | Wire ingestor into app startup lifecycle | `app/main.py` (updated) |

**Phase 4 checkpoint:**
- App logs price updates every 5 seconds
- `redis-cli GET price:AAPL` returns a price
- Changing a position symbol appears in the next ingestor cycle

---

## Phase 5 — WebSocket Layer ⬜

Goal: clients connect over WebSocket, authenticate, and stay subscribed to a portfolio.

| Step | What we build | Files |
|------|--------------|-------|
| ⬜ 5.1 | ConnectionManager — tracks live WebSocket connections by portfolio | `app/websocket/manager.py` |
| ⬜ 5.2 | WebSocket router + JWT auth | `app/websocket/router.py` |
| ⬜ 5.3 | Redis pub/sub subscriber — listens for price events | `app/websocket/subscriber.py` |
| ⬜ 5.4 | Wire WebSocket router and subscriber into app startup | `app/main.py` (updated) |

**Phase 5 checkpoint:**
- Connect with: `wscat -c "ws://localhost:8001/ws/portfolios/{id}?token={jwt}"`
- Connection stays open
- Server logs the connection

---

## Phase 6 — Calculator + Live Broadcast ⬜

Goal: when a price changes, affected clients receive a recalculated portfolio update in real time.

| Step | What we build | Files |
|------|--------------|-------|
| ⬜ 6.1 | Portfolio calculator — pure functions for P&L, market value, totals | `app/domain/portfolio/calculator.py` |
| ⬜ 6.2 | Wire calculator into the WebSocket broadcast path | `app/websocket/subscriber.py` (updated) |
| ⬜ 6.3 | Add current metrics to REST GET /portfolios/{id} response | `app/domain/portfolio/service.py` (updated) |

**Phase 6 checkpoint (the milestone):**
- Connect via WebSocket to a portfolio that holds AAPL
- Watch the ingestor tick
- Receive a message like:
  ```json
  {
    "portfolio_id": "...",
    "total_value": 18432.50,
    "positions": [
      { "symbol": "AAPL", "quantity": 10, "current_price": 189.42,
        "market_value": 1894.20, "unrealized_pnl": 94.20, "pnl_pct": 5.23 }
    ]
  }
  ```

---

## Phase 7 — Polish ⬜

Goal: the app behaves correctly under bad input and logs clearly in all cases.

| Step | What we build | Files |
|------|--------------|-------|
| ⬜ 7.1 | Request ID injected into every log line | `app/core/logging.py` (updated) |
| ⬜ 7.2 | Ownership checks — users cannot access other users' data | service layer (audit) |
| ⬜ 7.3 | Input edge cases — duplicate portfolio names, invalid symbols, zero quantity | service layer (audit) |
| ⬜ 7.4 | WebSocket cleanup — dead connections pruned on send failure | `app/websocket/manager.py` (updated) |

---

## Phase 8 — Tests ⬜

Goal: key paths are covered by automated tests.

| Step | What we build | Files |
|------|--------------|-------|
| ⬜ 8.1 | Test config + fixtures (test DB, test client) | `tests/conftest.py` |
| ⬜ 8.2 | Unit tests for the calculator (pure functions, no I/O) | `tests/unit/test_calculator.py` |
| ⬜ 8.3 | Integration tests for auth endpoints | `tests/integration/test_auth.py` |
| ⬜ 8.4 | Integration tests for portfolio + position CRUD | `tests/integration/test_portfolios.py` |
| ⬜ 8.5 | WebSocket integration test — connect, trigger price, assert message | `tests/integration/test_websocket.py` |

---

## Phase 9 — Frontend ⬜

Goal: a React dashboard shows live portfolio data updating in real time.

| Step | What we build | Files |
|------|--------------|-------|
| ⬜ 9.1 | Vite + React + Tailwind setup, added to docker-compose | `frontend/` scaffold |
| ⬜ 9.2 | REST API client wrapper | `frontend/src/api/` |
| ⬜ 9.3 | WebSocket client with reconnect logic | `frontend/src/ws/` |
| ⬜ 9.4 | Login + Register pages | `frontend/src/pages/` |
| ⬜ 9.5 | Portfolio list page | `frontend/src/pages/Portfolios.jsx` |
| ⬜ 9.6 | Portfolio detail page — live P&L table, connection status indicator | `frontend/src/pages/PortfolioDetail.jsx` |

**Phase 9 checkpoint:**
- Open browser, log in, create a portfolio, add positions
- Watch the P&L column update live without refreshing the page

---

## What's been built so far

```
✅ Phase 1 complete — stack runs, health endpoint green
⬜ Phase 2 — next up
```
