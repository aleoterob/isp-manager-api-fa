from fastapi import APIRouter

from app.features.app.router import router as app_router
from app.features.auth.router import router as auth_router
from app.features.customers.router import router as customers_router
from app.features.orders.router import router as orders_router
from app.features.users.router import router as users_router

api_router = APIRouter()
api_router.include_router(app_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(customers_router)
api_router.include_router(orders_router)
