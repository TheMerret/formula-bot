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
from src.services.search_service import SearchService
from src.services.formula_rag_service import FormulaRAGService
from langchain_gigachat.chat_models import GigaChat as LangChainGigaChat
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
    
    # Initialize Search Service (if enabled)
    search_service = None
    if settings.enable_search:
        search_service = SearchService(
            cache_repository=user_repo,
            max_results=settings.search_max_results,
            cache_ttl=settings.search_cache_ttl
        )
        logger.info("Search service initialized")
    
    # Initialize LangChain GigaChat for RAG service
    langchain_llm = LangChainGigaChat(
        credentials=settings.gigachat_key,
        scope=settings.gigachat_scope,
        model=settings.gigachat_model,
        temperature=0.1,
        verify_ssl_certs=False
    )
    
    # Initialize FormulaRAG Service (if enabled)
    formula_rag_service = None
    if settings.enable_rag:
        try:
            logger.info("Initializing FormulaRAG service...")
            formula_rag_service = FormulaRAGService(
                llm=langchain_llm,
                source_urls=settings.rag_source_urls,
                chunk_size=settings.rag_chunk_size,
                chunk_overlap=settings.rag_chunk_overlap,
                k=settings.rag_retrieval_k
            )
            await formula_rag_service.initialize()
            logger.info("FormulaRAG service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}", exc_info=True)
            logger.warning("Continuing without RAG service")
            formula_rag_service = None
    
    # Initialize GigaChat Service with search and RAG integration
    gigachat_service = GigaChatService(
        credentials=settings.gigachat_key,
        scope=settings.gigachat_scope,
        model=settings.gigachat_model,
        search_service=search_service,
        formula_rag_service=formula_rag_service
    )
    
    # Register middleware
    dp.message.middleware(RegistrationMiddleware(user_repo))
    
    # Register routers
    dp.include_router(common_router)
    dp.include_router(formula_router)
    
    # Register startup/shutdown handlers
    async def startup_handler():
        await on_startup(bot, user_repo)
    
    async def shutdown_handler():
        await on_shutdown(bot)
    
    dp.startup.register(startup_handler)
    dp.shutdown.register(shutdown_handler)
    
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