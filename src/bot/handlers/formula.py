"""Formula recognition handlers."""

import io
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from src.bot.keyboards import get_cancel_keyboard, get_main_menu_keyboard
from src.bot.states import BotStates
from src.services import GigaChatService

logger = logging.getLogger(__name__)

# Create router for formula handlers
router = Router(name="formula")


@router.message(Command("formula"))
@router.message(F.text == "📸 Распознать формулу")
async def cmd_formula(message: Message, state: FSMContext):
    """
    Handle /formula command and formula button - enter formula recognition mode.
    
    Args:
        message: Incoming message
        state: FSM context
    """
    await state.set_state(BotStates.waiting_for_formula)
    
    await message.answer(
        "📸 <b>Режим распознавания формулы</b>\n\n"
        "Отправьте мне фото формулы, и я объясню:\n"
        "• Что это за формула\n"
        "• Где она применяется\n"
        "• Что означает каждая переменная\n\n"
        "💡 <i>Для лучшего результата используйте четкое фото с хорошим освещением</i>\n\n"
        "Нажмите \"❌ Отмена\" для возврата в меню.",
        reply_markup=get_cancel_keyboard()
    )
    
    logger.info(f"User {message.from_user.id} entered formula recognition mode")


@router.message(BotStates.waiting_for_formula, F.photo)
async def handle_formula_photo(
    message: Message,
    state: FSMContext,
    gigachat_service: GigaChatService,
    bot
):
    """
    Handle photo in formula recognition mode.
    
    Args:
        message: Incoming message with photo
        state: FSM context
        gigachat_service: GigaChat service instance
        bot: Bot instance
    """
    user_id = message.from_user.id
    logger.info(f"User {user_id} sent a photo for formula recognition")
    
    try:
        # Get the largest photo
        photo = message.photo[-1]
        
        # Send processing message
        processing_msg = await message.answer(
            "⏳ Обрабатываю изображение...\n"
            "Это может занять несколько секунд."
        )
        
        # Download photo
        async with ChatActionSender(bot=bot, chat_id=message.chat.id, action="typing"):
            photo_file = await bot.download(photo.file_id)
            
            # Read photo bytes
            photo_bytes = photo_file.read()
            photo_io = io.BytesIO(photo_bytes)
            
            logger.info(f"Photo downloaded, size: {len(photo_bytes)} bytes")
            
            # Upload to GigaChat
            await processing_msg.edit_text(
                "⏳ Загружаю изображение в GigaChat...\n"
                "Пожалуйста, подождите."
            )
            
            file_id = await gigachat_service.upload_image(photo_io)
            logger.info(f"Image uploaded to GigaChat, file_id: {file_id}")
            
            # Recognize formula
            await processing_msg.edit_text(
                "🔍 Распознаю формулу и готовлю объяснение...\n"
                "Это займет около 10-20 секунд."
            )
            
            explanation = await gigachat_service.recognize_formula_with_search(file_id)
            
            # Delete processing message
            await processing_msg.delete()
            
            # Send explanation
            await message.answer(
                f"✅ <b>Результат распознавания:</b>\n\n{explanation}",
                reply_markup=get_main_menu_keyboard()
            )
            
            # Return to menu state
            await state.set_state(BotStates.menu)
            
            logger.info(f"Formula recognition completed for user {user_id}")
            
    except Exception as e:
        logger.error(f"Error processing formula for user {user_id}: {e}", exc_info=True)
        
        await message.answer(
            "❌ <b>Произошла ошибка при обработке изображения</b>\n\n"
            "Возможные причины:\n"
            "• Изображение слишком большое или повреждено\n"
            "• Проблемы с подключением к GigaChat API\n"
            "• Формула не распознана на изображении\n\n"
            "Попробуйте:\n"
            "• Отправить другое фото\n"
            "• Убедиться, что формула четко видна\n"
            "• Попробовать позже\n\n"
            f"Техническая информация: {str(e)}",
            reply_markup=get_main_menu_keyboard()
        )
        
        # Return to menu state
        await state.set_state(BotStates.menu)


@router.message(BotStates.waiting_for_formula)
async def handle_invalid_input(message: Message):
    """
    Handle invalid input in formula recognition mode.
    
    Args:
        message: Incoming message
    """
    await message.answer(
        "❌ Пожалуйста, отправьте <b>фото</b> формулы.\n\n"
        "Я могу обрабатывать только изображения.\n"
        "Используйте кнопку \"❌ Отмена\" для возврата в меню.",
        reply_markup=get_cancel_keyboard()
    )