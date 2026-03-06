"""Main entry point for the Formula Recognition Telegram Bot."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import settings
from src.database import UserRepository
from src.services import GigaChatService
from src.bot.middlewares import RegistrationMiddleware
from src.bot.handlers import common_router, formula_router
from src.utils import setup_logging

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, user_repo: UserRepository):
    """
    Actions to perform on bot startup.
    
    Args:
        bot: Bot instance
        user_repo: User repository
    """
    # Initialize database
    await user_repo.init_db()
    logger.info("Database initialized")
    
    # Get bot info
    bot_info = await bot.get_me()
    logger.info(f"Bot started: @{bot_info.username}")


async def on_shutdown(bot: Bot):
    """
    Actions to perform on bot shutdown.
    
    Args:
        bot: Bot instance
    """
    logger.info("Shutting down bot...")
    await bot.session.close()


async def main():
    """Main function to run the bot."""
    # Setup logging
    setup_logging(settings.log_level)
    
    logger.info("Starting Formula Recognition Bot...")
    logger.info(f"Configuration loaded from .env")
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Initialize services
    user_repo = UserRepository(settings.db_path)
    gigachat_service = GigaChatService(
        credentials=settings.gigachat_key,
        scope=settings.gigachat_scope,
        model=settings.gigachat_model
    )
    
    # Register middleware
    dp.message.middleware(RegistrationMiddleware(user_repo))
    
    # Register routers
    dp.include_router(common_router)
    dp.include_router(formula_router)
    
    # Register startup/shutdown handlers
    dp.startup.register(lambda: on_startup(bot, user_repo))
    dp.shutdown.register(lambda: on_shutdown(bot))
    
    # Inject dependencies into handlers
    # This makes user_repo, gigachat_service, and bot available in all handlers
    dp["user_repo"] = user_repo
    dp["gigachat_service"] = gigachat_service
    dp["bot"] = bot
    
    try:
        # Delete webhook and start polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Starting polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Error during bot execution: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)