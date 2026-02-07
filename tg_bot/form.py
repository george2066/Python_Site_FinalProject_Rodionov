from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


class Form(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()
