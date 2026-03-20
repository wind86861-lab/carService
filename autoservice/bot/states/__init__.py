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


class AdminSearch(StatesGroup):
    waiting_for_order = State()
    waiting_for_client = State()
    waiting_for_plate = State()


class AdminCreateMaster(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_username = State()
    waiting_for_password = State()
    waiting_for_phone = State()


class AdminNewMaster(StatesGroup):
    waiting_for_username = State()
    waiting_for_password = State()


class MasterCreateOrder(StatesGroup):
    waiting_for_brand = State()
    waiting_for_model = State()
    waiting_for_plate = State()
    waiting_for_color = State()
    waiting_for_year = State()
    waiting_for_client_name = State()
    waiting_for_client_phone = State()
    waiting_for_problem = State()
    waiting_for_work_desc = State()
    waiting_for_price = State()
    waiting_for_paid = State()
    waiting_for_photos = State()
    waiting_for_confirm = State()


class MasterCloseOrder(StatesGroup):
    waiting_for_parts_cost = State()
    waiting_for_confirm = State()


class MasterUpdateParts(StatesGroup):
    waiting_for_item_name = State()
    waiting_for_amount = State()
    waiting_for_receipt = State()
