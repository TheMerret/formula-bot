"""Common bot handlers (start, help, menu)."""

import logging

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.keyboards import get_main_menu_keyboard
from src.bot.states import BotStates
from src.database import UserRepository

logger = logging.getLogger(__name__)

# Create router for common handlers
router = Router(name="common")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user_repo: UserRepository):
    """
    Handle /start command - register user and show main menu.
    
    Args:
        message: Incoming message
        state: FSM context
        user_repo: User repository
    """
    user_id = message.from_user.id
    
    # Check if user already exists
    user_exists = await user_repo.user_exists(user_id)
    
    if not user_exists:
        # Register new user
        await user_repo.create_user(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        welcome_text = (
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "Вы успешно зарегистрированы!\n\n"
            "🤖 Я бот для распознавания математических формул.\n"
            "Отправьте мне фото формулы, и я объясню, что это за формула и где она применяется.\n\n"
            "Используйте кнопки меню ниже для навигации."
        )
        logger.info(f"New user registered: {user_id}")
    else:
        welcome_text = (
            f"👋 С возвращением, {message.from_user.first_name}!\n\n"
            "Вы уже зарегистрированы.\n\n"
            "Используйте кнопки меню ниже для навигации."
        )
        logger.info(f"Existing user started bot: {user_id}")
    
    # Set state to menu
    await state.set_state(BotStates.menu)
    
    # Send welcome message with keyboard
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    """
    Handle /help command and help button.
    
    Args:
        message: Incoming message
    """
    help_text = (
        "📖 <b>Справка по использованию бота</b>\n\n"
        
        "<b>Основные команды:</b>\n"
        "/start - Регистрация и главное меню\n"
        "/help - Показать эту справку\n"
        "/formula - Начать распознавание формулы\n"
        "/cancel - Отменить текущее действие\n\n"
        
        "<b>Как использовать:</b>\n"
        "1️⃣ Нажмите кнопку \"📸 Распознать формулу\" или используйте команду /formula\n"
        "2️⃣ Отправьте фото формулы (написанной от руки или из учебника)\n"
        "3️⃣ Дождитесь анализа - бот распознает формулу и предоставит подробное объяснение\n\n"
        
        "<b>Что бот может объяснить:</b>\n"
        "• Название формулы\n"
        "• Область применения (физика, математика, химия и т.д.)\n"
        "• Значение каждой переменной\n"
        "• Практическое применение\n"
        "• Примеры использования\n\n"
        
        "<b>Примеры формул:</b>\n"
        "• E = mc² (формула Эйнштейна)\n"
        "• F = ma (второй закон Ньютона)\n"
        "• a² + b² = c² (теорема Пифагора)\n"
        "• V = πr²h (объем цилиндра)\n\n"
        
        "💡 <i>Совет: Для лучшего распознавания делайте четкие фото с хорошим освещением!</i>"
    )
    
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())


@router.message(Command("cancel"))
@router.message(F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    """
    Handle /cancel command and cancel button - return to main menu.
    
    Args:
        message: Incoming message
        state: FSM context
    """
    current_state = await state.get_state()
    
    if current_state is None or current_state == BotStates.menu.state:
        await message.answer(
            "Нечего отменять. Вы уже в главном меню.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await state.set_state(BotStates.menu)
        await message.answer(
            "✅ Действие отменено. Возвращаемся в главное меню.",
            reply_markup=get_main_menu_keyboard()
        )
        logger.info(f"User {message.from_user.id} cancelled action from state: {current_state}")