"""Router aggregation for all bot handlers."""

from aiogram import Router

from .callbacks import router as callbacks_router
from .commands import router as commands_router
from .messages import router as messages_router

main_router = Router(name="main_router")
main_router.include_router(commands_router)
main_router.include_router(callbacks_router)
main_router.include_router(messages_router)
