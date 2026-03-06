"""FSM states for the bot."""

from aiogram.fsm.state import State, StatesGroup


class BotStates(StatesGroup):
    """Bot conversation states."""
    
    # Main menu state
    menu = State()
    
    # Formula recognition state - waiting for user to send an image
    waiting_for_formula = State()