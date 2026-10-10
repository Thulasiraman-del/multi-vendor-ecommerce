from fastapi import FastAPI
from sqlalchemy import text
from app.core.database import engine
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.vendors import router as vendors_router
from app.routes.categories import router as categories_router
from app.routes.products import router as products_router
from app.routes.cart import router as cart_router
from app.routes.orders import router as orders_router
app=FastAPI()
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(vendors_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
@app.get("/")
async def root():
    return {"message":"Multi Vendor Ecommerce API is running!"}
@app.get("/health")
async def health():
    return {"status": "healthy"}
@app.get("/db_health")
async def db_health():
    async with engine.connect() as conn:
        result=await conn.execute(text("SELECT 1"))
        return{"db_status":"healthy" if result.scalar()==1 else "unhealthy"
        }