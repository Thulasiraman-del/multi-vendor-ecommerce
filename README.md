# Multi-Vendor E-Commerce REST API
A Python backend project built with FastAPI and PostgreSQL to support a multi-vendor e-commerce platform.
## Features
- User registration and login
- JWT-based authentication
- User profile endpoint
- Vendor registration and vendor-specific access
- Product and category management
- Shopping cart operations
- Checkout and order creation
- Inventory stock validation and updates
- Customer order cancellation
- Vendor order fulfillment status updates
- Automated tests with pytest
- Database migrations with Alembic
## Tech Stack
- Python
- FastAPI
- PostgreSQL
- SQLAlchemy (async)
- Alembic
- Pydantic
- JWT authentication
- pytest
- Uvicorn
## Project Setup
### 1. Clone the repository
```bash
git clone https://github.com/Thulasiraman-del/multi-vendor-ecommerce.git
cd multi-vendor-ecommerce
```
### 2. Create and activate a virtual environment
Windows PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
### 3. Install dependencies
```powershell
python -m pip install -r requirements.txt
```
### 4. Configure environment variables
Create a `.env` file in the project root and configure `DATABASE_URL` for your PostgreSQL database.
Never commit `.env` or publish database passwords and secret keys.
### 5. Apply database migrations
```powershell
python -m alembic upgrade head
```
### 6. Start the API
```powershell
python -m uvicorn app.main:app --reload
```
### 7. Open API documentation
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health
## Run Tests
```powershell
python -m pytest -v
```
## Project Status
The API endpoints and core business logic have been implemented, and 36 automated tests passed in the latest recorded test run.
Further integration testing and deployment preparation can improve production readiness.
## Security
- Keep credentials and secret keys in environment variables.
- Use a separate test database for integration tests.
- Do not use real customer data in development or testing.
## Author
Thulasiraman Srinivasan

