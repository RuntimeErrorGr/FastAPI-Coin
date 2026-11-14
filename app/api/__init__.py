from app.api.routes import auth as auth_router
from app.api.routes import coins as coins_router
from app.api.routes import exchange as exchange_router
from app.api.routes import notifications as notifications_router
from app.api.routes import transfers as transfers_router
from app.api.routes import users as users_router
from app.api.routes import wallets as wallets_router

__all__ = [
    "auth_router",
    "coins_router",
    "exchange_router",
    "notifications_router",
    "transfers_router",
    "users_router",
    "wallets_router",
]
