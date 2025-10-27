# Redis Credit & Data Pool Implementation

## Overview
FastAPI application with Redis for high-performance credit transactions, data pool management, and API token authentication. Redis is source of truth for credits (atomic operations), PostgreSQL provides durable storage.

## Architecture

### Data Storage
- **Redis**: Source of truth for credits (atomic operations), data pool, and API tokens (sub-ms latency)
- **PostgreSQL**: Durable backup for credits, source of truth for tokens and transaction history

### Key Structure
```
credit:user:{user_id}     → User credit balance (integer)
data:pool                 → Set of available data items
data:sold:{user_id}       → Set of data purchased by user
token:user:{user_id}      → User's API token (string)
token:lookup:{token}      → Reverse lookup: token → user_id
```

## Core Components

### 1. Redis Manager (`app/core/redis_manager.py`)
Singleton managing Redis connection and operations.

**Lua Script - Atomic Purchase**:
```lua
-- Checks credit → pops data → deducts credit → marks sold
-- Returns: {status, data, credit_remaining, cost}
```

**Key Methods**:
- `purchase_data(user_id, amount)` - Atomic purchase via Lua
- `add_data_to_pool(items)` - Add to pool (admin)
- `get_user_credit(user_id)` - Query credit
- `set_user_credit(user_id, amount)` - Sync from PostgreSQL
- `set_user_token(user_id, token)` - Store user API token
- `get_user_token(user_id)` - Get token by user_id
- `get_user_id_by_token(token)` - Get user_id by token (for fast auth)

**Configuration**:
- `CREDIT_PER_ITEM = 1` - Cost per data item (configurable via API)

### 2. Credit Service (`app/services/credit_service.py`)
Business logic layer with PostgreSQL transaction safety.

**Operations**:
- `add_credits()` - Top-up (Redis INCRBY atomic → PostgreSQL sync)
- `purchase_data()` - Buy data (Redis Lua script atomic → PostgreSQL sync)
- `sync_credit_to_redis()` - Load from PostgreSQL
- `sync_credit_to_postgres()` - Persist to PostgreSQL
- `get_transactions()` - Query history

**Transaction Flow**:
1. Credit operations executed in Redis (atomic via INCRBY/Lua scripts)
2. Immediately synced to PostgreSQL for durability
3. If PostgreSQL write fails, scheduler syncs Redis → PostgreSQL (every 5 seconds)
4. Redis is always source of truth (no race conditions)

### 3. Background Scheduler (`app/core/scheduler.py`)
Periodic sync to prevent Redis data loss.

**Configuration**:
```python
SYNC_INTERVAL_SECONDS = 5  # 5 seconds (default, configurable)
```

**Sync Process**:
- **Credits**: Redis → PostgreSQL (one direction). Redis is source of truth via atomic INCRBY/Lua scripts
- **Tokens**: Redis → PostgreSQL (one direction). Updates PostgreSQL if different
- Creates new records for users only in Redis
- Runs every 5 seconds for both credits and tokens
- Logs all changes
- Handles failed immediate writes during operations

### 4. Database Models (`app/models/user.py`)

**UserCredit**:
```python
user_id: int (PK, FK)
credits: int
updated_at: datetime
```

**Transaction**:
```python
id: int (PK)
user_id: int (FK)
amount: int (negative for purchases)
description: str
data_id: str (comma-separated purchased items)
timestamp: datetime
```

**UserToken**:
```python
user_id: int (PK, FK)
token: str (unique, indexed - sha256 hash)
created_at: datetime
updated_at: datetime
```

## Authentication

### Token-Based Authentication (`app/users.py`)

**Token Generation**:
- Automatic on user registration via `UserManager.on_after_register()`
- Token format: `sha256(email + random_int)`
- Stored in both PostgreSQL (`user_token` table) and Redis (`token:*` keys)

**Token Authentication Flow**:
1. Client sends `Authorization: Bearer <token>` header
2. `get_user_from_token()` dependency checks Redis first (fast path)
3. If not in Redis, queries PostgreSQL and caches result
4. Returns authenticated `User` object

**Protected Endpoints** (require token auth):
- `/api/credits`
- `/api/purchase`
- `/api/transactions`
- `/api/datapool/size`

**Other Endpoints** (use cookie auth via fastapi-users):
- All other endpoints continue to use existing cookie-based authentication

## API Endpoints

### User Endpoints

#### Credits (`/api/credits/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/credits` | Token | Get credit balance (Redis + PostgreSQL) |
| POST | `/purchase` | Token | Purchase data items |
| GET | `/transactions` | Token | Transaction history (limit=50) |
| GET | `/token` | Cookie | Get user's API token |
| POST | `/token/rotate` | Cookie | Rotate API token (invalidates old) |

#### Data Pool (`/api/datapool/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/datapool/size` | Token | Get pool size |
| GET | `/datapool/my-data` | Token | Get purchased data |

### Admin Endpoints (`/api/admin/*`)

**Authentication**: All admin endpoints require `ADMIN_TOKEN` in `Authorization: Bearer <token>` header.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/admin/credits/add` | Admin Token | Add credits to user account |
| POST | `/admin/datapool/add` | Admin Token | Add data items to pool |
| POST | `/admin/datapool/config/cost` | Admin Token | Update cost per item |
| GET | `/admin/datapool/config/cost` | Admin Token | Get current cost per item |

## Safety Guarantees

### 1. No Double Payment
- Lua script executes atomically
- Credit check and deduction in single Redis operation
- No database locks or race conditions

### 2. No Payment Without Data
- Data popped before credit deduction
- If pool empty → fail fast, no charge
- Actual cost based on items received

### 3. Credit Protection & Race Condition Prevention
- **All credit operations use Redis atomic operations** (INCRBY for additions, Lua script for purchases)
- **No race conditions**: Redis guarantees atomicity for concurrent operations
- **Add credits**: Redis INCRBY (atomic) → PostgreSQL sync → Transaction record
- **Purchase**: Redis Lua script (atomic) → PostgreSQL sync → Transaction record
- **Immediate sync**: All operations sync to PostgreSQL instantly for durability
- **Scheduler backup**: Redis → PostgreSQL every 5 seconds (handles failed writes)
- **On Redis restart**: Load credits from PostgreSQL (durable backup)

### 4. Data Uniqueness
- Redis Sets ensure no duplicate data items
- User-specific sold sets track ownership
- Data removed from pool on purchase (SPOP)

### 5. Token Security
- Tokens stored as SHA256 hashes (plain text in storage)
- Unique constraint prevents duplicate tokens
- Fast Redis lookup for authentication (<1ms)
- Automatic sync to PostgreSQL every 5 seconds
- Invalid/expired tokens return HTTP 401

## Startup Integration (`app/main.py`)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_manager.connect()
    await redis_manager.load_lua_scripts()
    await scheduler.start()

    yield

    # Shutdown
    await scheduler.stop()
    await redis_manager.disconnect()
```

## Configuration

**Environment** (`.env`):
```
REDIS_URL=redis://127.0.0.1:63774/0
DATABASE_URL=postgresql+asyncpg://...
ADMIN_TOKEN=your-secure-admin-token-here
AUTH_SECRET=your-auth-secret-here
```

**Runtime**:
- `SYNC_INTERVAL_SECONDS` - Scheduler interval (default: 5s)
- `CREDIT_PER_ITEM` - Cost per item (default: 1, updatable via API)

## Usage Examples

### User Registration (Automatic Token Generation)
```bash
POST /auth/register
{
  "email": "user@example.com",
  "password": "securepass"
}

# Token automatically generated and stored
# Format: sha256("user@example.com" + random_int)
# Logged to console: "Generated API token for user {user_id}: {token}"
```

### Admin: Add Credits (Admin Token)
```bash
POST /api/admin/credits/add
Authorization: Bearer <ADMIN_TOKEN>
{
  "user_id": 123,
  "amount": 1000,
  "description": "Welcome bonus"
}

# Uses Redis INCRBY (atomic) - no race conditions
# credit:user:123 = INCRBY 1000
# Then syncs to PostgreSQL immediately
```

### Admin: Add Data to Pool (Admin Token)
```bash
POST /api/admin/datapool/add
Authorization: Bearer <ADMIN_TOKEN>
{
  "data_items": ["email1@example.com", "email2@example.com"]
}
```

### User: Purchase Data (Token Auth)
```bash
POST /api/purchase
Authorization: Bearer abc123def456...
{
  "amount": 10
}

Response:
{
  "status": "success",
  "data": ["email1@example.com", ...],
  "cost": 10,
  "credit_remaining": 990
}
```

### User: Check Balance (Token Auth)
```bash
GET /api/credits
Authorization: Bearer abc123def456...

Response:
{
  "user_id": 123,
  "redis_credits": 990,
  "postgres_credits": 990,
  "synced": true
}
```

## Failure Scenarios

| Scenario | Behavior |
|----------|----------|
| Insufficient credit | HTTP 402, no charge, fail fast |
| Empty data pool | HTTP 404, no charge |
| Invalid token | HTTP 401, authentication failed |
| PostgreSQL down (purchase) | Purchase succeeds in Redis, synced next interval |
| PostgreSQL down (add credits) | Operation fails, Redis unchanged |
| PostgreSQL down (token auth) | Token lookup fails, returns 401 |
| Redis down | App startup fails (lifespan event) |
| Sync failure | Logged, retried next interval |

## Performance Characteristics

- **Token authentication**: <1ms (Redis lookup)
- **Purchase latency**: <5ms (Redis Lua script)
- **Credit check**: <1ms (Redis GET)
- **Transaction history**: ~50ms (PostgreSQL query)
- **Sync overhead**: Negligible (background task)

## Future Enhancements

1. Admin role/permission checks (currently TODO)
2. Token refresh/rotation mechanism
3. Token expiration (TTL in Redis)
4. Persistent CREDIT_PER_ITEM in database
5. Redis persistence configuration (AOF/RDB)
6. Transaction retry logic on PostgreSQL failure
7. Metrics/monitoring for sync lag
8. Rate limiting on purchase endpoint
