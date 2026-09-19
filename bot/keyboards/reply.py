from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="💼 بخش استخدام و جذب نیرو"), KeyboardButton(text="🛍️ کاتالوگ و محصولات")],
        [KeyboardButton(text="🤝 پنل و کد اختصاصی بازاریاب"), KeyboardButton(text="📞 پشتیبانی و تماس")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="⚙️ پنل مدیریت")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_recruitment_menu() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📝 ثبت درخواست استخدام جدید")],
        [KeyboardButton(text="🔍 پیگیری وضعیت استخدام"), KeyboardButton(text="📜 شرایط و مدارک مورد نیاز")],
        [KeyboardButton(text="🔙 بازگشت به منوی اصلی")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_marketer_menu() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🔗 دریافت لینک و کد اختصاصی من")],
        [KeyboardButton(text="📊 آمار و گزارش عملکرد من"), KeyboardButton(text="📦 دریافت پکیج‌های تبلیغاتی")],
        [KeyboardButton(text="🔙 بازگشت به منوی اصلی")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_contact_request_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📱 ارسال شماره تلفن همراه من", request_contact=True)],
        [KeyboardButton(text="❌ انصراف و بازگشت")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_cancel_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="❌ انصراف و بازگشت")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_finish_docs_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="✅ اتمام ارسال مدارک و مرحله بعد")],
        [KeyboardButton(text="❌ انصراف و بازگشت")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_confirm_app_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="✅ تأیید نهایی و ارسال برای مدیریت")],
        [KeyboardButton(text="❌ انصراف و لغو درخواست")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
