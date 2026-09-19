from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_rules_agreement_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ قوانین را خواندم و می‌پذیرم", callback_data="rules_agree"),
                InlineKeyboardButton(text="❌ انصراف", callback_data="rules_decline")
            ]
        ]
    )

def get_admin_app_review_kb(app_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تأیید استخدام", callback_data=f"adm_app_approve_{app_id}"),
                InlineKeyboardButton(text="❌ رد درخواست", callback_data=f"adm_app_reject_{app_id}")
            ],
            [
                InlineKeyboardButton(text="⚠️ اعلام نقص مدارک", callback_data=f"adm_app_needinfo_{app_id}"),
                InlineKeyboardButton(text="📂 مشاهده مدارک ارسالی", callback_data=f"adm_app_docs_{app_id}")
            ]
        ]
    )

def get_product_nav_kb(current_index: int, total_count: int, product_id: int, marketer_ref: str = "") -> InlineKeyboardMarkup:
    buttons = []
    
    # دکمه‌های اقدام محصول
    action_row = [
        InlineKeyboardButton(
            text="📥 پکیج بازاریابی (عکس + متن فروش)", 
            callback_data=f"prod_pkg_{product_id}_{marketer_ref or 'none'}"
        )
    ]
    buttons.append(action_row)

    # دکمه ثبت سفارش / مشاوره خرید
    contact_row = [
        InlineKeyboardButton(
            text="💬 هماهنگی خرید / استعلام موجودی", 
            callback_data=f"prod_order_{product_id}"
        )
    ]
    buttons.append(contact_row)

    # ناوبری بین محصولات
    nav_row = []
    if current_index > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ قبلی", callback_data=f"prod_page_{current_index - 1}"))
    
    nav_row.append(InlineKeyboardButton(text=f"📌 {current_index + 1} از {total_count}", callback_data="noop"))

    if current_index < total_count - 1:
        nav_row.append(InlineKeyboardButton(text="بعدی ➡️", callback_data=f"prod_page_{current_index + 1}"))
    
    buttons.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_supplementary_doc_upload_kb(app_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 ارسال مدارک تکمیلی", callback_data=f"upload_supp_{app_id}")]
        ]
    )
