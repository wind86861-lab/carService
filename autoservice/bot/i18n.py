"""Internationalization strings for the AutoService bot (Uzbek / Russian)."""

STRINGS: dict[str, dict[str, str]] = {
    "uz": {
        # --- Registration / Start ---
        "choose_language": "🌐 Tilni tanlang / Выберите язык:",
        "language_saved": "✅ Til saqlandi: O'zbek",
        "ask_phone": "📱 Boshlash uchun telefon raqamingizni yuboring:",
        "phone_saved": "✅ Telefon raqam saqlandi!",
        "welcome_client": "👋 Xush kelibsiz, {name}!\nMashinangizni kuzatish uchun quyidagi menyudan foydalaning.",
        "welcome_master": "👋 Xush kelibsiz, {name}! Siz usta sifatida kirdingiz.",
        "welcome_admin": "👋 Xush kelibsiz, {name}! Siz administrator sifatida kirdingiz.",
        "car_linked_ok": "✅ Mashinangiz muvaffaqiyatli bog'landi!",
        "help_client": (
            "/start — botni qayta ishga tushirish\n"
            "/language — tilni o'zgartirish\n\n"
            "🚗 Mashina holati — mashinangiz holatini tekshirish\n"
            "🔗 Buyurtmaga bog'lanish — mavjud buyurtmaga bog'lanish\n"
            "📋 Mening buyurtmalarim — buyurtmalar tarixi"
        ),
        "help_master": (
            "/start — botni qayta ishga tushirish\n"
            "/language — tilni o'zgartirish\n\n"
            "🆕 Yangi buyurtma — yangi buyurtma yaratish\n"
            "📋 Mening buyurtmalarim — faol buyurtmalar\n"
            "📊 Statistika — ish ko'rsatkichlaringiz"
        ),
        "help_admin": (
            "/start — botni qayta ishga tushirish\n"
            "/language — tilni o'zgartirish\n\n"
            "📊 Boshqaruv paneli — umumiy statistika\n"
            "📋 Barcha buyurtmalar — boshqaruv\n"
            "👥 Mijozlar / 🔧 Ustalar — foydalanuvchilarni boshqarish\n"
            "📢 Xabar yuborish — ommaviy xabar"
        ),
        "unknown_message": "Kechirasiz, tushunmadim. /help — mavjud buyruqlar.",
        # --- Status labels ---
        "status_new": "🆕 Yangi",
        "status_preparation": "🔧 Tayyorlash",
        "status_in_process": "⚙️ Jarayonda",
        "status_ready": "✅ Tayyor",
        "status_closed": "🏁 Yopildi",
        # --- Notifications to client ---
        "notif_preparation": (
            "🔧 <b>Buyurtma {order_number}</b> ({car_info})\n\n"
            "Mashinangizni ta'mirlash boshlandi. Ish tayyorlanmoqda."
        ),
        "notif_in_process": (
            "⚙️ <b>Buyurtma {order_number}</b> ({car_info})\n\n"
            "Mashinangiz ustida ish jarayonda."
        ),
        "notif_ready": (
            "✅ <b>Buyurtma {order_number}</b> ({car_info})\n\n"
            "Mashinangiz tayyor. Olib ketishingiz mumkin! 🚗"
        ),
        "notif_receipt_request": (
            "📋 <b>Buyurtma {order_number}</b>\n\n"
            "Usta buyurtmani tugalladi. Mashinangizni qabul qildingizmi?"
        ),
        "notif_status_generic": (
            "<b>Buyurtma {order_number}</b>\n\n"
            "Holat yangilandi: {status}"
        ),
        # --- Notifications to master ---
        "notif_master_receipt_confirmed": (
            "✅ <b>Buyurtma {order_number}</b>\n\n"
            "Mijoz mashinani qabul qilganini tasdiqladi. Buyurtma to'liq yopildi."
        ),
        "notif_master_dispute": (
            "⚠️ <b>Buyurtma {order_number}</b>\n\n"
            "Mijoz {client_name} muammo haqida xabar berdi. Iltimos, bog'laning."
        ),
        # --- Feedback ---
        "feedback_request": (
            "⭐ <b>Buyurtma {order_number}</b>\n\n"
            "Xizmatimizni qanday baholaysiz? 1 dan 10 gacha baho bering."
        ),
        "feedback_rated": "⭐ Siz xizmatni baholadingiz: {rating}/10",
        "feedback_ask_positive": "😊 Xizmatimizning qaysi jihati yoqdi?",
        "feedback_ask_negative": "😔 Kechirasiz. Asosiy muammo nima edi?",
        "feedback_ask_comment": "💬 Izoh qo'shmoqchimisiz? Yozing yoki O'tkazib yuborish.",
        "feedback_thanks": "🙏 Fikr-mulohazangiz uchun rahmat!",
        "feedback_saved": "✅ Rahmat! Fikr-mulohazangiz saqlandi.",
        # --- Positive feedback categories ---
        "pos_quality": "✅ Sifat",
        "pos_speed": "⚡ Tezlik",
        "pos_price": "💰 Narx",
        "pos_communication": "💬 Muloqot",
        # --- Negative feedback categories ---
        "cat_communication": "💬 Muloqot",
        "cat_time": "⏱ Vaqt",
        "cat_quality": "🔧 Sifat",
        "cat_price": "💰 Narx",
        "cat_other": "📝 Boshqa",
        "cat_skip": "⏭ O'tkazib yuborish",
        # --- Order card (client view) ---
        "order_card": (
            "<b>Buyurtma: {order_number}</b>\n"
            "──────────────────────\n"
            "Mashina:   {car_name}\n"
            "Raqam:     {plate}\n"
            "──────────────────────\n"
            "Muammo:    {problem}\n"
            "Ish:       {work_desc}\n"
            "──────────────────────\n"
            "Holat:     {status}\n"
            "Narx:      {price}\n"
            "To'landi:  {paid}\n"
            "Sana:      {date}"
        ),
        "order_card_expenses": "\n──────────────────────\n🔩 Xarajatlar:\n{expenses}",
        "order_summary": "<b>{order_number}</b> | {car_name} | {status} | {date}",
        # --- Client no orders ---
        "no_active_orders": "Hozirda faol buyurtmalaringiz yo'q.",
        "no_orders": "Sizda hali buyurtmalar yo'q.",
        "enter_order_number": "Buyurtma raqamingizni kiriting (masalan, A-00123):",
        "order_not_found": "❌ Buyurtma topilmadi. Raqamni tekshirib, qayta urinib ko'ring.",
        # --- Confirmation ---
        "confirm_receipt_done": "✅ Siz mashinani qabul qilganingizni tasdiqladingiz. Buyurtma yopildi.",
        "already_confirmed": "✅ Siz allaqachon qabul qilganingizni tasdiqlagansiz.",
        "dispute_reported": "⚠️ Biz ustani sizning muammo haqida xabardor qildik.",
        # --- Misc ---
        "cancelled": "❌ Bekor qilindi.",
        "error_generic": "❌ Xato yuz berdi. Iltimos, qayta urinib ko'ring.",
    },

    "ru": {
        # --- Registration / Start ---
        "choose_language": "🌐 Tilni tanlang / Выберите язык:",
        "language_saved": "✅ Язык сохранён: Русский",
        "ask_phone": "📱 Для начала отправьте свой номер телефона:",
        "phone_saved": "✅ Номер телефона сохранён!",
        "welcome_client": "👋 Добро пожаловать, {name}!\nИспользуйте меню ниже для отслеживания вашего автомобиля.",
        "welcome_master": "👋 Добро пожаловать, {name}! Вы вошли как мастер.",
        "welcome_admin": "👋 Добро пожаловать, {name}! Вы вошли как администратор.",
        "car_linked_ok": "✅ Ваш автомобиль успешно привязан!",
        "help_client": (
            "/start — перезапустить бота\n"
            "/language — сменить язык\n\n"
            "🚗 Статус авто — проверить статус ремонта\n"
            "🔗 Привязать заказ — привязать существующий заказ\n"
            "📋 Мои заказы — история заказов"
        ),
        "help_master": (
            "/start — перезапустить бота\n"
            "/language — сменить язык\n\n"
            "🆕 Новый заказ — создать новый заказ\n"
            "📋 Мои заказы — активные заказы\n"
            "📊 Статистика — ваши показатели"
        ),
        "help_admin": (
            "/start — перезапустить бота\n"
            "/language — сменить язык\n\n"
            "📊 Панель управления — общая статистика\n"
            "📋 Все заказы — управление заказами\n"
            "👥 Клиенты / 🔧 Мастера — управление пользователями\n"
            "📢 Рассылка — массовая рассылка"
        ),
        "unknown_message": "Извините, не понял. /help — доступные команды.",
        # --- Status labels ---
        "status_new": "🆕 Новый",
        "status_preparation": "🔧 Подготовка",
        "status_in_process": "⚙️ В процессе",
        "status_ready": "✅ Готов",
        "status_closed": "🏁 Закрыт",
        # --- Notifications to client ---
        "notif_preparation": (
            "🔧 <b>Заказ {order_number}</b> ({car_info})\n\n"
            "Ремонт вашего автомобиля начался. Идёт подготовка."
        ),
        "notif_in_process": (
            "⚙️ <b>Заказ {order_number}</b> ({car_info})\n\n"
            "Ремонт вашего автомобиля в процессе."
        ),
        "notif_ready": (
            "✅ <b>Заказ {order_number}</b> ({car_info})\n\n"
            "Ваш автомобиль готов. Можете забрать! 🚗"
        ),
        "notif_receipt_request": (
            "📋 <b>Заказ {order_number}</b>\n\n"
            "Мастер завершил заказ. Вы получили свой автомобиль?"
        ),
        "notif_status_generic": (
            "<b>Заказ {order_number}</b>\n\n"
            "Статус обновлён: {status}"
        ),
        # --- Notifications to master ---
        "notif_master_receipt_confirmed": (
            "✅ <b>Заказ {order_number}</b>\n\n"
            "Клиент подтвердил получение автомобиля. Заказ полностью закрыт."
        ),
        "notif_master_dispute": (
            "⚠️ <b>Заказ {order_number}</b>\n\n"
            "Клиент {client_name} сообщил о проблеме. Пожалуйста, свяжитесь с ним."
        ),
        # --- Feedback ---
        "feedback_request": (
            "⭐ <b>Заказ {order_number}</b>\n\n"
            "Как вы оцениваете наш сервис? Дайте оценку от 1 до 10."
        ),
        "feedback_rated": "⭐ Вы оценили сервис: {rating}/10",
        "feedback_ask_positive": "😊 Что вам понравилось в нашем сервисе?",
        "feedback_ask_negative": "😔 Извините. В чём была основная проблема?",
        "feedback_ask_comment": "💬 Хотите добавить комментарий? Напишите или нажмите Пропустить.",
        "feedback_thanks": "🙏 Спасибо за ваш отзыв!",
        "feedback_saved": "✅ Спасибо! Ваш отзыв сохранён.",
        # --- Positive feedback categories ---
        "pos_quality": "✅ Качество",
        "pos_speed": "⚡ Скорость",
        "pos_price": "💰 Цена",
        "pos_communication": "💬 Общение",
        # --- Negative feedback categories ---
        "cat_communication": "💬 Общение",
        "cat_time": "⏱ Время",
        "cat_quality": "🔧 Качество",
        "cat_price": "💰 Цена",
        "cat_other": "📝 Другое",
        "cat_skip": "⏭ Пропустить",
        # --- Order card (client view) ---
        "order_card": (
            "<b>Заказ: {order_number}</b>\n"
            "──────────────────────\n"
            "Авто:      {car_name}\n"
            "Номер:     {plate}\n"
            "──────────────────────\n"
            "Проблема:  {problem}\n"
            "Работа:    {work_desc}\n"
            "──────────────────────\n"
            "Статус:    {status}\n"
            "Цена:      {price}\n"
            "Оплачено:  {paid}\n"
            "Дата:      {date}"
        ),
        "order_card_expenses": "\n──────────────────────\n🔩 Расходы:\n{expenses}",
        "order_summary": "<b>{order_number}</b> | {car_name} | {status} | {date}",
        # --- Client no orders ---
        "no_active_orders": "У вас нет активных заказов.",
        "no_orders": "У вас ещё нет заказов.",
        "enter_order_number": "Введите номер заказа (например, A-00123):",
        "order_not_found": "❌ Заказ не найден. Проверьте номер и попробуйте снова.",
        # --- Confirmation ---
        "confirm_receipt_done": "✅ Вы подтвердили получение автомобиля. Заказ закрыт.",
        "already_confirmed": "✅ Вы уже подтвердили получение.",
        "dispute_reported": "⚠️ Мы уведомили мастера о вашей проблеме.",
        # --- Misc ---
        "cancelled": "❌ Отменено.",
        "error_generic": "❌ Произошла ошибка. Пожалуйста, попробуйте снова.",
    },
}


def t(key: str, lang: str = "uz", **kwargs) -> str:
    """Return translated string for key in given language, falling back to 'uz'."""
    text = STRINGS.get(lang, STRINGS["uz"]).get(key) or STRINGS["uz"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def lang_of(db_user) -> str:
    """Extract language code from a db_user dict, defaulting to 'uz'."""
    if isinstance(db_user, dict):
        return db_user.get("language") or "uz"
    return "uz"
