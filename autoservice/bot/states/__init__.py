from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_phone = State()


class ClientLinkOrder(StatesGroup):
    waiting_for_order_number = State()


class ClientFeedback(StatesGroup):
    waiting_for_rating = State()
    waiting_for_category = State()
    waiting_for_comment = State()


class AdminBroadcast(StatesGroup):
    waiting_for_target = State()
    waiting_for_message = State()
    waiting_for_confirm = State()
