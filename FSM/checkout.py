from aiogram.fsm.state import StatesGroup, State


class CheckoutStates(StatesGroup):
    enter_name = State()
    enter_phone = State()
    enter_address = State()
