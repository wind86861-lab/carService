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
        # --- Reply keyboard buttons ---
        "btn_cancel": "❌ Bekor qilish",
        "btn_send_phone": "📱 Telefon raqamini yuborish",
        "btn_new_order": "🆕 Yangi buyurtma",
        "btn_my_orders": "📋 Mening buyurtmalarim",
        "btn_closed_orders": "📁 Yopilgan buyurtmalar",
        "btn_statistics": "📊 Statistika",
        "btn_car_status": "🚗 Mashina holati",
        "btn_link_order": "🔗 Buyurtmaga bog'lanish",
        "btn_dashboard": "📊 Boshqaruv paneli",
        "btn_all_orders": "📋 Barcha buyurtmalar",
        "btn_clients": "👥 Mijozlar",
        "btn_masters": "🔧 Ustalar",
        "btn_finance": "💰 Moliya",
        "btn_car_history": "🚗 Mashina tarixi",
        "btn_new_master": "➕ Yangi usta",
        "btn_broadcast": "📢 Xabar yuborish",
        # --- Master new order FSM ---
        "new_order_title": "🆕 <b>Yangi buyurtma</b>\n\n1️⃣ Mashina <b>markasini</b> kiriting:\n(masalan: Chevrolet, BYD)",
        "step_model": "2️⃣ Mashina <b>modelini</b> kiriting:",
        "step_plate": "3️⃣ Davlat <b>raqamini</b> kiriting:\n(masalan: 01A123BB)",
        "step_color": "4️⃣ Mashina <b>rangini</b> kiriting yoki /skip:",
        "step_year": "5️⃣ Ishlab chiqarilgan <b>yilini</b> kiriting yoki /skip:",
        "err_invalid_year": "❗ To'g'ri yil kiriting (masalan: 2018) yoki /skip",
        "step_client_name": "6️⃣ Mijozning <b>ismi</b>:",
        "step_client_phone": "7️⃣ Mijozning <b>telefon raqami</b>:\n(masalan: +998901234567)",
        "err_invalid_phone": "❗ To'g'ri telefon raqam kiriting:",
        "step_problem": "8️⃣ <b>Muammo / nosozlik</b> tavsifini kiriting:",
        "step_work_desc": "9️⃣ <b>Bajariladigan ishlar</b> ro'yxatini kiriting yoki /skip:",
        "step_price": "🔟 Xizmat <b>narxini</b> kiriting (so'm):",
        "err_invalid_amount": "❗ Faqat raqam kiriting (masalan: 150000):",
        "step_paid": "1️⃣1️⃣ Oldindan to'lov (<b>avans</b>) miqdori (so'm):\n(masalan: 50000, yoki 0)",
        "err_paid_too_much": "❗ Avans ({paid:,}) narxdan ({price:,}) ko'p bo'lishi mumkin emas. Qaytadan kiriting:",
        "step_photos": "1️⃣2️⃣ <b>Mashina rasmlarini</b> yuboring (1-2 ta).\nTugatish uchun /done, o'tkazib yuborish uchun /skip:",
        "photo_prompt": "Rasm yuboring yoki /done / /skip:",
        "photo_received": "✅ {count} ta rasm qabul qilindi. Yana 1 ta yuboring yoki /done:",
        "photos_done": "✅ 2 ta rasm qabul qilindi.",
        "order_confirm_prompt": "Tasdiqlash uchun <b>Ha</b>, bekor qilish uchun <b>Yo'q</b> yuboring.",
        "order_created": "✅ <b>Buyurtma yaratildi!</b>\n\nBuyurtma raqami: <b>{order_number}</b>\nMashina: {car}\nMijoz: {client_name} | {client_phone}\nMuammo: {problem}\nNarx: {price:,} so'm | Avans: {paid:,} so'm",
        "share_link_msg": "📤 <b>Mijozga havola:</b>\nQuyidagi tugmani bosib havolani mijozga yuboring.\n\n<code>{link}</code>",
        "share_btn": "📤 Mijozga havola yuborish",
        "share_btn_linked": "✅ Mijoz bog'langan",
        "order_create_error": "❌ Buyurtma yaratishda xato yuz berdi.",
        # --- Master order list ---
        "no_active_orders_master": "📋 <b>Faol buyurtmalar yo'q.</b>",
        "my_orders_header": "📋 <b>Mening buyurtmalarim</b> ({total} ta faol)\nSahifa {page}/{total_pages}",
        "no_closed_orders_master": "📁 <b>Yopilgan buyurtmalar yo'q.</b>",
        "closed_orders_header": "📁 <b>Yopilgan buyurtmalar</b> ({total} ta)\n\n",
        "no_access": "Ruxsat yo'q.",
        "order_not_found_short": "Buyurtma topilmadi.",
        # --- Master order detail labels ---
        "order_lbl_status": "Holat",
        "order_lbl_car": "Mashina",
        "order_lbl_client": "Mijoz",
        "order_lbl_problem": "Muammo",
        "order_lbl_work": "Ish",
        "order_lbl_price": "Narx",
        "order_lbl_advance": "Avans",
        "order_lbl_confirmed": "Mijoz tasdiqladi",
        "order_lbl_date": "Sana",
        "order_lbl_master": "Usta",
        "order_lbl_parts": "Ehtiyot qismlar",
        "order_lbl_profit": "Foyda",
        "order_lbl_closed_at": "Yopildi",
        # --- Master status / close ---
        "status_updated": "✅ Holat yangilandi!",
        "cant_change_status": "Bu holat o'zgartirib bo'lmaydi.",
        "client_not_confirmed": "Mijoz hali tasdiqlamagan.",
        "financial_report": "📊 <b>Moliyaviy hisobot — {order_number}</b>\n\nKelishilgan narx:   <b>{agreed:,} so'm</b>\nEhtiyot qismlar:    <b>{parts:,} so'm</b>\nFoyda:              <b>{profit:,} so'm</b>\nSizning ulushingiz: <b>{master_share:,} so'm</b> ({master_pct}%)\nXizmat ulushi:      <b>{service_share:,} so'm</b> ({service_pct}%)\n\nTasdiqlash uchun <b>Ha</b>, qayta kiritish uchun <b>Yo'q</b>.",
        "parts_cost_prompt": "💰 <b>{order_number}</b>\n\nKelishilgan narx: <b>{agreed}</b>\n\nEhtiyot qismlar narxini (so'm) kiriting yoki 0:",
        "err_invalid_parts": "❗ Faqat raqam kiriting (masalan: 30000 yoki 0):",
        "parts_retry": "Ehtiyot qismlar narxini qaytadan kiriting:",
        "order_closed_success": "✅ <b>{order_number}</b> muvaffaqiyatli yopildi!\n\nSizning ulushingiz: <b>{share:,} so'm</b>",
        "order_closed_error": "❌ Buyurtmani yopishda xato yuz berdi.",
        "admin_order_closed_msg": "💰 <b>Buyurtma yopildi — {order_number}</b>\n\nUsta: {master_name}\nEhtiyot qismlar: {parts:,} so'm\nFoyda: {profit:,} so'm\nMaster ulushi: {master_share:,} so'm\nXizmat ulushi: {service_share:,} so'm",
        # --- Master add expense ---
        "parts_add_title": "🔩 <b>{order_number}</b> — Xarajat qo'shish\n\nHozirgi jami xarajat: <b>{current:,} so'm</b>\n\n1️⃣ Xarajat <b>nomini</b> kiriting:\n(masalan: Balon salidor, Moy filtri)",
        "parts_step_amount": "2️⃣ Narxini kiriting (so'm):\n(masalan: 3000)",
        "err_positive_amount": "❗ 0 dan katta raqam kiriting:",
        "parts_step_receipt": "3️⃣ <b>Chek rasmini</b> yuboring yoki /skip:",
        "parts_photo_prompt": "Rasm yuboring yoki /skip:",
        "parts_closed_error": "Yopilgan buyurtmaga qo'shib bo'lmaydi.",
        "parts_added": "✅ <b>{order_number}</b> — xarajat qo'shildi!\n\n📦 {item_name}: <b>{amount:,} so'm</b>\n{receipt_note}\nJami xarajat: <b>{total:,} so'm</b>",
        "receipt_saved": "📷 Chek saqlandi",
        "parts_add_error": "❌ Xato yuz berdi.",
        # --- Master statistics ---
        "no_statistics": "Bu oy hali yopilgan buyurtmalar yo'q.",
        "statistics_report": "📊 <b>Shu oygi statistikangiz:</b>\n\nYopilgan buyurtmalar: <b>{orders}</b>\nJami daromad:         <b>{revenue}</b>\nEhtiyot qismlar:      <b>{parts}</b>\nFoyda:                <b>{profit}</b>\nSizning ulushingiz:   <b>{share}</b>",
        # --- Admin ---
        "dashboard": "<b>📊 Boshqaruv paneli</b>\n\n🔄 Faol buyurtmalar: <b>{active}</b>\n✅ Tayyor buyurtmalar: <b>{ready}</b>\n\n💰 Shu oy daromad: <b>{revenue}</b>\n📈 Shu oy foyda: <b>{profit}</b>\n\n👤 Faol mijozlar: <b>{clients}</b>\n🔧 Faol ustalar: <b>{masters}</b>",
        "dashboard_error": "❌ Statistikani yuklashda xato.",
        "all_orders_header": "📋 <b>Barcha buyurtmalar</b> ({total} ta) — Sahifa {page}/{total_pages}",
        "orders_load_error": "❌ Buyurtmalarni yuklashda xato.",
        "order_search_prompt": "🔍 Buyurtma raqami, davlat raqami yoki mijoz ismini kiriting:",
        "order_search_done": "✅ Qidiruv tugadi.",
        "order_search_none": "❌ Buyurtma topilmadi.",
        "force_close_confirm": "⚠️ <b>{order_number}</b> buyurtmani majburiy yopasizmi?\n\nWeb panel orqali qismlar narxini kiriting:\n{web_url}/admin/orders",
        "force_close_redirect": "⚠️ Majburiy yopish uchun web panelni oching:\n{web_url}/admin/orders",
        "clients_search_prompt": "👥 <b>Mijozlarni qidirish</b>\n\nIsm yoki telefon kiriting, yoki barcha uchun <b>.</b> yuboring:",
        "no_clients": "❌ Mijoz topilmadi.",
        "clients_header": "👥 <b>Mijozlar</b> ({total} ta):",
        "client_not_found_adm": "❌ Mijoz topilmadi.",
        "status_active": "✅ Faol",
        "status_blocked": "🚫 Bloklangan",
        "client_detail": "👤 <b>{name}</b>\nHolat: {status}\nTelefon: {phone}\nTelegram ID: <code>{tg_id}</code>\nUsername: {username}\n\n📋 Jami buyurtmalar: <b>{total}</b>\n✅ Yopilgan: <b>{closed}</b>\n💰 Jami summa: <b>{revenue}</b>",
        "no_masters_adm": "🔧 Hech qanday usta topilmadi.",
        "masters_header": "🔧 <b>Ustalar</b> ({total} ta):",
        "master_not_found_adm": "❌ Usta topilmadi.",
        "master_detail": "🔧 <b>{name}</b>\nHolat: {status}\nTelefon: {phone}\nUsername: {username}\nTelegram ID: <code>{tg_id}</code>\n\n📋 Jami buyurtmalar: <b>{total}</b>\n✅ Yopilgan: <b>{closed}</b>\n💰 Jami daromad: <b>{revenue}</b>",
        "user_blocked_msg": "🚫 Foydalanuvchi #{target} bloklandi.",
        "user_unblocked_msg": "✅ Foydalanuvchi #{target} blokdan chiqarildi.",
        "user_promoted_msg": "⬆️ Foydalanuvchi #{target} ustaga ko'tarildi.",
        "credentials_sent": "\n✉️ Kirish ma'lumotlari Telegram orqali yuborildi.",
        "user_demoted_msg": "⬇️ Usta #{target} mijozga tushirildi.",
        "confirm_action": "Tasdiqlang",
        "action_cancelled": "❌ Bekor qilindi.",
        "action_error": "❌ Xato yuz berdi.",
        "new_master_title": "👥 <b>Yangi usta uchun mijoz tanlang</b> ({total} ta)\nSahifa {page}/{total_pages}:",
        "new_master_selected": "👤 <b>{name}</b> tanlandi.\nTelefon: {phone}\n\nUsername kiriting (yoki /skip):",
        "new_master_pwd_prompt": "Parol kiriting (yoki /skip):",
        "username_taken": "❌ '{username}' username allaqachon mavjud. /skip yoki boshqa username kiriting.",
        "master_promoted_success": "✅ <b>{name}</b> ustaga ko'tarildi!\n\nUsername: <code>{username}</code>\nParol: <code>{password}</code>\nKirish: {web_url}/login",
        "master_promote_error": "❌ Xato yuz berdi.",
        "master_credentials_msg": "Tabriklaymiz! Siz usta sifatida tayinlandingiz.\n\nWeb panelga kirish:\n{web_url}/login\n\nUsername: {username}\nPassword: {password}\n\nTizimga kirgach parolingizni o'zgartiring.",
        "financials_title": "💰 <b>Moliya hisoboti</b>\n\nDavrni tanlang:",
        "financials_report": "💰 <b>Moliya hisoboti — {period}</b>\n\n📋 Buyurtmalar: <b>{orders}</b>\n💵 Daromad: <b>{revenue}</b>\n🔩 Qismlar: <b>{parts}</b>\n📈 Foyda: <b>{profit}</b>\n🔧 Usta ulushi: <b>{master_share}</b>",
        "financials_error": "❌ Moliya ma'lumotlarini yuklashda xato.",
        "period_today": "Bugun", "period_week": "Hafta", "period_month": "Oy", "period_year": "Yil",
        "car_history_prompt": "🚗 <b>Mashina tarixi</b>\n\nDavlat raqamini kiriting (masalan: 01A123BB):",
        "car_not_found": "❌ <b>{plate}</b> raqamli mashina tarixida buyurtma topilmadi.",
        "car_history_header": "🚗 <b>{plate}</b> {brand} — {count} ta tashrif\n",
        "broadcast_title": "📢 <b>Ommaviy xabar</b>\n\nMaqsadli auditoriyani tanlang:",
        "broadcast_audience_set": "Auditoriya: <b>{audience}</b>\n\nYubormoqchi bo'lgan xabarni kiriting:",
        "broadcast_preview": "📢 <b>Xabarni tasdiqlash</b>\n\nAuditoriya: <b>{audience}</b>\n\nXabar:\n<i>{text}</i>\n\nYuborasizmi?",
        "broadcast_sending": "⏳ Xabar yuborilmoqda…",
        "broadcast_done": "✅ <b>Xabar yuborildi!</b>\n\nYetkazildi: <b>{sent}</b>\nXato: <b>{failed}</b>",
        "broadcast_error": "❌ Xabar yuborishda xato.",
        "audience_all": "Barcha", "audience_clients": "Faqat mijozlar", "audience_masters": "Faqat ustalar",
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
        # --- Reply keyboard buttons ---
        "btn_cancel": "❌ Отмена",
        "btn_send_phone": "📱 Отправить номер телефона",
        "btn_new_order": "🆕 Новый заказ",
        "btn_my_orders": "📋 Мои заказы",
        "btn_closed_orders": "📁 Закрытые заказы",
        "btn_statistics": "📊 Статистика",
        "btn_car_status": "🚗 Статус авто",
        "btn_link_order": "🔗 Привязать заказ",
        "btn_dashboard": "📊 Панель управления",
        "btn_all_orders": "📋 Все заказы",
        "btn_clients": "👥 Клиенты",
        "btn_masters": "🔧 Мастера",
        "btn_finance": "💰 Финансы",
        "btn_car_history": "🚗 История авто",
        "btn_new_master": "➕ Новый мастер",
        "btn_broadcast": "📢 Рассылка",
        # --- Master new order FSM ---
        "new_order_title": "🆕 <b>Новый заказ</b>\n\n1️⃣ Введите <b>марку</b> автомобиля:\n(например: Chevrolet, BYD)",
        "step_model": "2️⃣ Введите <b>модель</b> автомобиля:",
        "step_plate": "3️⃣ Введите <b>госномер</b>:\n(например: 01A123BB)",
        "step_color": "4️⃣ Введите <b>цвет</b> или /skip:",
        "step_year": "5️⃣ Введите <b>год выпуска</b> или /skip:",
        "err_invalid_year": "❗ Введите корректный год (например: 2018) или /skip",
        "step_client_name": "6️⃣ <b>Имя клиента</b>:",
        "step_client_phone": "7️⃣ <b>Телефон клиента</b>:\n(например: +998901234567)",
        "err_invalid_phone": "❗ Введите корректный номер телефона:",
        "step_problem": "8️⃣ Опишите <b>проблему / неисправность</b>:",
        "step_work_desc": "9️⃣ Введите список <b>работ</b> или /skip:",
        "step_price": "🔟 Введите <b>стоимость</b> услуги (сум):",
        "err_invalid_amount": "❗ Введите только число (например: 150000):",
        "step_paid": "1️⃣1️⃣ Сумма <b>аванса</b> (сум):\n(например: 50000 или 0)",
        "err_paid_too_much": "❗ Аванс ({paid:,}) не может превышать стоимость ({price:,}). Введите снова:",
        "step_photos": "1️⃣2️⃣ Отправьте <b>фото автомобиля</b> (1-2 шт.).\n/done — завершить, /skip — пропустить:",
        "photo_prompt": "Отправьте фото или /done / /skip:",
        "photo_received": "✅ Получено {count} фото. Отправьте ещё 1 или /done:",
        "photos_done": "✅ Получено 2 фото.",
        "order_confirm_prompt": "Для подтверждения — <b>Да</b>, для отмены — <b>Нет</b>.",
        "order_created": "✅ <b>Заказ создан!</b>\n\nНомер заказа: <b>{order_number}</b>\nАвто: {car}\nКлиент: {client_name} | {client_phone}\nПроблема: {problem}\nЦена: {price:,} сум | Аванс: {paid:,} сум",
        "share_link_msg": "📤 <b>Ссылка для клиента:</b>\nНажмите кнопку ниже и отправьте ссылку клиенту.\n\n<code>{link}</code>",
        "share_btn": "📤 Отправить ссылку клиенту",
        "share_btn_linked": "✅ Клиент привязан",
        "order_create_error": "❌ Ошибка при создании заказа.",
        # --- Master order list ---
        "no_active_orders_master": "📋 <b>Активных заказов нет.</b>",
        "my_orders_header": "📋 <b>Мои заказы</b> ({total} активных)\nСтраница {page}/{total_pages}",
        "no_closed_orders_master": "📁 <b>Закрытых заказов нет.</b>",
        "closed_orders_header": "📁 <b>Закрытые заказы</b> ({total} шт.)\n\n",
        "no_access": "Нет доступа.",
        "order_not_found_short": "Заказ не найден.",
        # --- Master order detail labels ---
        "order_lbl_status": "Статус",
        "order_lbl_car": "Авто",
        "order_lbl_client": "Клиент",
        "order_lbl_problem": "Проблема",
        "order_lbl_work": "Работа",
        "order_lbl_price": "Цена",
        "order_lbl_advance": "Аванс",
        "order_lbl_confirmed": "Клиент подтвердил",
        "order_lbl_date": "Дата",
        "order_lbl_master": "Мастер",
        "order_lbl_parts": "Запчасти",
        "order_lbl_profit": "Прибыль",
        "order_lbl_closed_at": "Закрыт",
        # --- Master status / close ---
        "status_updated": "✅ Статус обновлён!",
        "cant_change_status": "Этот статус нельзя изменить.",
        "client_not_confirmed": "Клиент ещё не подтвердил.",
        "financial_report": "📊 <b>Финансовый отчёт — {order_number}</b>\n\nСогласованная цена: <b>{agreed:,} сум</b>\nЗапчасти:           <b>{parts:,} сум</b>\nПрибыль:            <b>{profit:,} сум</b>\nВаша доля:          <b>{master_share:,} сум</b> ({master_pct}%)\nДоля сервиса:       <b>{service_share:,} сум</b> ({service_pct}%)\n\nДля подтверждения — <b>Да</b>, для повтора — <b>Нет</b>.",
        "parts_cost_prompt": "💰 <b>{order_number}</b>\n\nСогласованная цена: <b>{agreed}</b>\n\nВведите стоимость запчастей (сум) или 0:",
        "err_invalid_parts": "❗ Введите только число (например: 30000 или 0):",
        "parts_retry": "Введите стоимость запчастей снова:",
        "order_closed_success": "✅ <b>{order_number}</b> успешно закрыт!\n\nВаша доля: <b>{share:,} сум</b>",
        "order_closed_error": "❌ Ошибка при закрытии заказа.",
        "admin_order_closed_msg": "💰 <b>Заказ закрыт — {order_number}</b>\n\nМастер: {master_name}\nЗапчасти: {parts:,} сум\nПрибыль: {profit:,} сум\nДоля мастера: {master_share:,} сум\nДоля сервиса: {service_share:,} сум",
        # --- Master add expense ---
        "parts_add_title": "🔩 <b>{order_number}</b> — Добавить расход\n\nТекущие расходы: <b>{current:,} сум</b>\n\n1️⃣ Введите <b>название</b> запчасти:\n(например: Шина, Масляный фильтр)",
        "parts_step_amount": "2️⃣ Введите стоимость (сум):\n(например: 3000)",
        "err_positive_amount": "❗ Введите число больше 0:",
        "parts_step_receipt": "3️⃣ Отправьте <b>фото чека</b> или /skip:",
        "parts_photo_prompt": "Отправьте фото или /skip:",
        "parts_closed_error": "Нельзя добавить к закрытому заказу.",
        "parts_added": "✅ <b>{order_number}</b> — расход добавлен!\n\n📦 {item_name}: <b>{amount:,} сум</b>\n{receipt_note}\nИтого расходов: <b>{total:,} сум</b>",
        "receipt_saved": "📷 Чек сохранён",
        "parts_add_error": "❌ Произошла ошибка.",
        # --- Master statistics ---
        "no_statistics": "В этом месяце закрытых заказов нет.",
        "statistics_report": "📊 <b>Статистика за этот месяц:</b>\n\nЗакрытые заказы: <b>{orders}</b>\nОбщий доход:     <b>{revenue}</b>\nЗапчасти:        <b>{parts}</b>\nПрибыль:         <b>{profit}</b>\nВаша доля:       <b>{share}</b>",
        # --- Admin ---
        "dashboard": "<b>📊 Панель управления</b>\n\n🔄 Активные заказы: <b>{active}</b>\n✅ Готовые заказы: <b>{ready}</b>\n\n💰 Доход за месяц: <b>{revenue}</b>\n📈 Прибыль за месяц: <b>{profit}</b>\n\n👤 Активные клиенты: <b>{clients}</b>\n🔧 Активные мастера: <b>{masters}</b>",
        "dashboard_error": "❌ Ошибка при загрузке статистики.",
        "all_orders_header": "📋 <b>Все заказы</b> ({total} шт.) — Страница {page}/{total_pages}",
        "orders_load_error": "❌ Ошибка при загрузке заказов.",
        "order_search_prompt": "🔍 Введите номер заказа, госномер или имя клиента:",
        "order_search_done": "✅ Поиск завершён.",
        "order_search_none": "❌ Заказ не найден.",
        "force_close_confirm": "⚠️ Принудительно закрыть заказ <b>{order_number}</b>?\n\nВведите стоимость запчастей через веб-панель:\n{web_url}/admin/orders",
        "force_close_redirect": "⚠️ Для принудительного закрытия откройте веб-панель:\n{web_url}/admin/orders",
        "clients_search_prompt": "👥 <b>Поиск клиентов</b>\n\nВведите имя или телефон, или <b>.</b> для показа всех:",
        "no_clients": "❌ Клиент не найден.",
        "clients_header": "👥 <b>Клиенты</b> ({total} шт.):",
        "client_not_found_adm": "❌ Клиент не найден.",
        "status_active": "✅ Активен",
        "status_blocked": "🚫 Заблокирован",
        "client_detail": "👤 <b>{name}</b>\nСтатус: {status}\nТелефон: {phone}\nTelegram ID: <code>{tg_id}</code>\nUsername: {username}\n\n📋 Всего заказов: <b>{total}</b>\n✅ Закрытых: <b>{closed}</b>\n💰 Общая сумма: <b>{revenue}</b>",
        "no_masters_adm": "🔧 Мастеров не найдено.",
        "masters_header": "🔧 <b>Мастера</b> ({total} шт.):",
        "master_not_found_adm": "❌ Мастер не найден.",
        "master_detail": "🔧 <b>{name}</b>\nСтатус: {status}\nТелефон: {phone}\nUsername: {username}\nTelegram ID: <code>{tg_id}</code>\n\n📋 Всего заказов: <b>{total}</b>\n✅ Закрытых: <b>{closed}</b>\n💰 Общий доход: <b>{revenue}</b>",
        "user_blocked_msg": "🚫 Пользователь #{target} заблокирован.",
        "user_unblocked_msg": "✅ Пользователь #{target} разблокирован.",
        "user_promoted_msg": "⬆️ Пользователь #{target} повышен до мастера.",
        "credentials_sent": "\n✉️ Данные входа отправлены через Telegram.",
        "user_demoted_msg": "⬇️ Мастер #{target} понижен до клиента.",
        "confirm_action": "Подтвердите",
        "action_cancelled": "❌ Отменено.",
        "action_error": "❌ Произошла ошибка.",
        "new_master_title": "👥 <b>Выберите клиента для нового мастера</b> ({total} шт.)\nСтраница {page}/{total_pages}:",
        "new_master_selected": "👤 <b>{name}</b> выбран.\nТелефон: {phone}\n\nВведите username (или /skip):",
        "new_master_pwd_prompt": "Введите пароль (или /skip):",
        "username_taken": "❌ Username '{username}' уже занят. Введите другой или /skip.",
        "master_promoted_success": "✅ <b>{name}</b> повышен до мастера!\n\nUsername: <code>{username}</code>\nПароль: <code>{password}</code>\nВход: {web_url}/login",
        "master_promote_error": "❌ Произошла ошибка.",
        "master_credentials_msg": "Поздравляем! Вы назначены мастером.\n\nВход в веб-панель:\n{web_url}/login\n\nUsername: {username}\nPassword: {password}\n\nПосле входа смените пароль.",
        "financials_title": "💰 <b>Финансовый отчёт</b>\n\nВыберите период:",
        "financials_report": "💰 <b>Финансовый отчёт — {period}</b>\n\n📋 Заказы: <b>{orders}</b>\n💵 Доход: <b>{revenue}</b>\n🔩 Запчасти: <b>{parts}</b>\n📈 Прибыль: <b>{profit}</b>\n🔧 Доля мастеров: <b>{master_share}</b>",
        "financials_error": "❌ Ошибка при загрузке финансовых данных.",
        "period_today": "Сегодня", "period_week": "Неделя", "period_month": "Месяц", "period_year": "Год",
        "car_history_prompt": "🚗 <b>История авто</b>\n\nВведите госномер (например: 01A123BB):",
        "car_not_found": "❌ По номеру <b>{plate}</b> заказов не найдено.",
        "car_history_header": "🚗 <b>{plate}</b> {brand} — {count} визита\n",
        "broadcast_title": "📢 <b>Рассылка</b>\n\nВыберите аудиторию:",
        "broadcast_audience_set": "Аудитория: <b>{audience}</b>\n\nВведите текст сообщения:",
        "broadcast_preview": "📢 <b>Подтверждение рассылки</b>\n\nАудитория: <b>{audience}</b>\n\nСообщение:\n<i>{text}</i>\n\nОтправить?",
        "broadcast_sending": "⏳ Отправка сообщения…",
        "broadcast_done": "✅ <b>Сообщение отправлено!</b>\n\nДоставлено: <b>{sent}</b>\nОшибок: <b>{failed}</b>",
        "broadcast_error": "❌ Ошибка при рассылке.",
        "audience_all": "Всем", "audience_clients": "Только клиентам", "audience_masters": "Только мастерам",
        # --- Misc ---
        "cancelled": "❌ Отменено.",
        "error_generic": "❌ Произошла ошибка. Пожалуйста, попробуйте снова.",
    },
}


def all_variants(key: str) -> set:
    """Return all language variants of a key (for handler filter matching)."""
    return {v for lang in STRINGS for v in [STRINGS[lang].get(key)] if v}


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
