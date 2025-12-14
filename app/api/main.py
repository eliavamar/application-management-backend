from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils, item_types, typed_items
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(item_types.router)
api_router.include_router(typed_items.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
