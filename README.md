# Multi-Vendor E-Commerce REST API

An asynchronous REST API for a multi-vendor e-commerce platform, built with Python, FastAPI, PostgreSQL, and SQLAlchemy.

The application supports customer authentication, vendor product management, shopping carts, order processing, inventory validation, and role-based access control.

## Features

### Authentication and Authorization
- User registration and login
- JWT access and refresh tokens
- Refresh-token rotation and revocation
- Secure password hashing
- Authenticated user profile endpoint
- Role-based access control (RBAC)
- Administrator-only category creation
- Secure first-administrator bootstrap script

### Product and Vendor Management
- Vendor profile creation and management
- Vendor-specific product management
- Product and category APIs
- Product search and filtering
- Price-range filtering
- Sorting and pagination
- Product ownership validation

### Shopping and Order Management
- Shopping cart creation and management
- Add, update, and remove cart items
- Checkout and order creation
- Inventory and stock validation
- Order cancellation with stock restoration
- Vendor-specific order access
- Order fulfillment status transitions

### Database and Testing
- Asynchronous SQLAlchemy database operations
- PostgreSQL persistence
- Alembic database migrations
- Database indexes for frequently queried fields
- Automated API and security tests with pytest
- SQLite-based isolated test database

### Docker
- Dockerized FastAPI application
- PostgreSQL service using Docker Compose
- PostgreSQL health checks
- API startup dependency on database health
- Persistent PostgreSQL volume

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| API Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy (Async) |
| Data Validation | Pydantic |
| Authentication | JWT |
| Password Hashing | pwdlib |
| Migrations | Alembic |
| Testing | Pytest |
| ASGI Server | Uvicorn |
| Containerization | Docker |
| Orchestration | Docker Compose |

## Project Structure

```text
multi-vendor-ecommerce/
├── alembic/
│   └── versions/
├── app/
│   ├── core/
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── scripts/
│   └── create_admin.py
├── tests/
├── .dockerignore
├── .gitignore
├── compose.yaml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Getting Started

### Option 1: Run with Docker Compose

Prerequisites:
- Docker Desktop
- Docker Compose

1. Clone the repository:

```bash
git clone https://github.com/Thulasiraman-del/multi-vendor-ecommerce.git
cd multi-vendor-ecommerce
```

2. Create a `.env` file in the project root:

```dotenv
POSTGRES_PASSWORD=replace_with_a_secure_database_password
DOCKER_DATABASE_URL=postgresql+asyncpg://ecommerce_user:replace_with_a_secure_database_password@db:5432/multivendor_db
DOCKER_SECRET_KEY=replace_with_a_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Use the same database password in `POSTGRES_PASSWORD` and `DOCKER_DATABASE_URL`. URL-encode special characters in the connection URL when necessary.

Never commit `.env` or publish secret values.

3. Build and start containers:

```powershell
docker compose up -d --build
```

4. Apply database migrations:

```powershell
docker compose exec api alembic upgrade head
```

5. Check container status:

```powershell
docker compose ps
```

6. Open API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Option 2: Run Locally

Prerequisites:
- Python 3.10 or compatible newer version
- PostgreSQL

1. Clone the repository:

```bash
git clone https://github.com/Thulasiraman-del/multi-vendor-ecommerce.git
cd multi-vendor-ecommerce
```

2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

4. Configure `.env`:

```dotenv
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/multivendor_db
SECRET_KEY=replace_with_a_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_ECHO=false
```

5. Apply migrations:

```powershell
python -m alembic upgrade head
```

6. Start the API:

```powershell
python -m uvicorn app.main:app --reload
```

## Administrator Bootstrap

The project includes a protected first-administrator creation script.

With Docker Compose:

```powershell
docker compose run --rm --no-deps api python -m scripts.create_admin
```

The script:
- Accepts the administrator password through hidden input.
- Requires password confirmation.
- Enforces a minimum password length.
- Prevents creating another administrator if one already exists.
- Uses a PostgreSQL advisory transaction lock to serialize concurrent bootstrap attempts.

Do not expose administrator credentials or JWT tokens.

## API Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /auth/register` | Register a customer |
| `POST /auth/login` | Authenticate a user |
| `POST /auth/refresh` | Refresh access credentials |
| `POST /auth/logout` | Revoke a refresh token |
| `GET /users/me` | Retrieve authenticated user |
| `POST /vendors` | Create vendor profile |
| `GET /vendors/me` | Retrieve vendor profile |
| `GET /categories` | List categories |
| `POST /categories` | Create category (admin only) |
| `/products` | Product listing and management |
| `/cart` | Shopping cart operations |
| `POST /orders/checkout` | Create an order |
| `/orders/` | Customer order operations |
| `GET /health` | Application health check |
| `GET /db_health` | Database connectivity check |

See Swagger UI for request schemas, response models, and the complete endpoint list.

## Running Tests

Run the complete automated test suite:

```powershell
python -m pytest -v
```

Latest verified test result (November 10, 2026):
- 68 tests passed
- 0 tests failed

Test coverage includes authentication, refresh-token security, authorization, products, categories, carts, checkout, order fulfillment, cancellation, and database behavior.

## Database Migrations

Check the current migration:

```powershell
python -m alembic current
```

Apply migrations:

```powershell
python -m alembic upgrade head
```

Check model and database schema consistency:

```powershell
python -m alembic check
```

## Health Checks

Application health:

```text
GET /health
```

Database connectivity:

```text
GET /db_health
```

## Security Practices

- Store credentials and secret keys in environment variables.
- Keep `.env` out of version control.
- Hash passwords before database storage.
- Validate JWT token types and expiration.
- Revoke refresh tokens during logout.
- Enforce role-based access control.
- Validate product ownership and inventory operations.
- Keep SQL query logging disabled by default.
- Use a separate test database for testing.

## Project Status

The project includes asynchronous REST APIs, JWT authentication, refresh-token management, role-based authorization, vendor and product management, shopping cart operations, order processing, PostgreSQL migrations, Docker Compose, and automated tests.

The latest local test suite passed all 68 tests. Docker API health, database connectivity, and Alembic schema consistency were also verified.

This is a portfolio and learning project. Further improvements can include CI/CD automation, deployment hardening, observability, and performance testing.

## Author

**Thulasiraman Srinivasan**

GitHub: https://github.com/Thulasiraman-del
