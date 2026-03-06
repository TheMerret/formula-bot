"""Custom middlewares for the bot."""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.database import UserRepository

logger = logging.getLogger(__name__)


class RegistrationMiddleware(BaseMiddleware):
    """Middleware to check if user is registered before processing messages."""
    
    def __init__(self, user_repo: UserRepository):
        """
        Initialize the middleware.
        
        Args:
            user_repo: User repository instance
        """
        super().__init__()
        self.user_repo = user_repo
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """
        Check registration before processing message.
        
        Args:
            handler: Next handler in the chain
            event: Incoming message
            data: Additional data
            
        Returns:
            Handler result or None if user not registered
        """
        # Skip check for /start command
        if event.text and event.text.startswith('/start'):
            return await handler(event, data)
        
        # Check if user is registered
        user_id = event.from_user.id
        is_registered = await self.user_repo.user_exists(user_id)
        
        if not is_registered:
            await event.answer(
                "❌ Вы не зарегистрированы!\n\n"
                "Пожалуйста, используйте команду /start для регистрации."
            )
            logger.warning(f"Unregistered user {user_id} tried to use the bot")
            return
        
        # User is registered, proceed with handler
        return await handler(event, data)