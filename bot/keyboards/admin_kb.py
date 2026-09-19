from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📋 بررسی درخواست‌های استخدام"), KeyboardButton(text="➕ افزودن محصول جدید")],
        [KeyboardButton(text="📦 مدیریت موجودی و محصولات"), KeyboardButton(text="👥 آمار بازاریاب‌ها و فروش")],
        [KeyboardButton(text="💎 مشتریان رتبه A و B"), KeyboardButton(text="📢 ارسال پیام همگانی")],
        [KeyboardButton(text="🔙 بازگشت به منوی اصلی")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_finish_product_photos_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="✅ اتمام ارسال تصاویر و ثبت نهایی")],
        [KeyboardButton(text="❌ انصراف از افزودن محصول")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_product_manage_inline_kb(product_id: int, is_available: bool) -> InlineKeyboardMarkup:
    status_text = "🔴 ناموجود کردن" if is_available else "🟢 موجود کردن"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=status_text, callback_data=f"toggle_prod_avail_{product_id}"),
                InlineKeyboardButton(text="🗑️ حذف محصول", callback_data=f"del_prod_{product_id}")
            ]
        ]
    )

def get_broadcast_target_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 همه کاربران", callback_data="bc_all"),
                InlineKeyboardButton(text="🤝 فقط بازاریاب‌ها", callback_data="bc_marketers")
            ],
            [
                InlineKeyboardButton(text="💼 متقاضیان استخدام", callback_data="bc_applicants"),
                InlineKeyboardButton(text="❌ انصراف", callback_data="bc_cancel")
            ]
        ]
    )
