"""Keyboard layouts for the bot."""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Get the main menu keyboard.
    
    Returns:
        ReplyKeyboardMarkup with main menu buttons
    """
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="📸 Распознать формулу")
    builder.button(text="ℹ️ Помощь")
    
    builder.adjust(2)  # 2 buttons per row
    
    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Get keyboard with cancel button.
    
    Returns:
        ReplyKeyboardMarkup with cancel button
    """
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="❌ Отмена")
    
    return builder.as_markup(resize_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    """
    Remove keyboard.
    
    Returns:
        ReplyKeyboardRemove object
    """
    return ReplyKeyboardRemove()