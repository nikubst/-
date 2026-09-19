from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from config import settings
from database.models import User, JobApplication, Product, Marketer
from keyboards.reply import get_cancel_kb, get_main_menu
from keyboards.admin_kb import (
    get_admin_main_kb,
    get_finish_product_photos_kb,
    get_product_manage_inline_kb,
    get_broadcast_target_kb
)
from keyboards.inline import get_admin_app_review_kb, get_supplementary_doc_upload_kb
from utils.states import AddProductStates, AdminReviewStates, BroadcastStates

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


# ------------------ مدیریت درخواست‌های استخدام ------------------

@router.message(F.text == "📋 بررسی درخواست‌های استخدام")
async def list_pending_applications(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    stmt = select(JobApplication).where(JobApplication.status == "pending").order_by(desc(JobApplication.created_at)).limit(10)
    result = await session.execute(stmt)
    apps = result.scalars().all()

    if not apps:
        await message.answer("✅ هیچ درخواست جدید یا در انتظار بررسی وجود ندارد.", reply_markup=get_admin_main_kb())
        return

    await message.answer(f"📋 تعداد {len(apps)} درخواست در انتظار بررسی یافت شد:")
    
    for app in apps:
        text = (
            f"👤 **متقاضی:** {app.full_name} (کد: `{app.tracking_code}`)\n"
            f"💼 **موقعیت:** {app.job_position}\n"
            f"📱 **تلفن:** {app.phone}\n"
            f"🆔 **کدملی:** {app.national_id}\n"
            f"🏙️ **شهر:** {app.city} (سن: {app.age})\n"
            f"📝 **سوابق:** {app.experience}\n"
            f"📂 **مدارک:** {len(app.documents)} مدرک پیوست شده\n"
            f"📅 **تاریخ:** {app.created_at.strftime('%Y/%m/%d %H:%M')}"
        )
        await message.answer(text, reply_markup=get_admin_app_review_kb(app.id), parse_mode="Markdown")


@router.callback_query(F.data.startswith("adm_app_docs_"))
async def show_application_docs(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return

    app_id = int(callback.data.replace("adm_app_docs_", ""))
    app_res = await session.execute(select(JobApplication).where(JobApplication.id == app_id))
    app = app_res.scalar_one_or_none()

    if not app:
        await callback.answer("درخواست یافت نشد.", show_alert=True)
        return

    docs = app.documents
    if not docs:
        await callback.message.answer("⚠️ مدرکی برای این پرونده یافت نشد.")
        await callback.answer()
        return

    await callback.message.answer(f"📂 در حال ارسال {len(docs)} مدرک مربوط به {app.full_name}:")
    for doc in docs:
        try:
            if doc.get("type") == "photo":
                await callback.message.answer_photo(photo=doc["file_id"])
            elif doc.get("type") == "document":
                await callback.message.answer_document(document=doc["file_id"])
        except Exception as e:
            await callback.message.answer(f"خطا در ارسال فایل: {e}")

    await callback.answer()


@router.callback_query(F.data.startswith("adm_app_approve_"))
async def approve_application(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return

    app_id = int(callback.data.replace("adm_app_approve_", ""))
    app_res = await session.execute(select(JobApplication).where(JobApplication.id == app_id))
    app = app_res.scalar_one_or_none()

    if not app:
        await callback.answer("یافت نشد.", show_alert=True)
        return

    app.status = "approved"
    app.admin_notes = "پرونده شما در ارزیابی اولیه تأیید گردید. به زودی جهت هماهنگی جلسه و مصاحبه با شما تماس گرفته خواهد شد."
    await session.commit()

    # اطلاع به متقاضی
    user_res = await session.execute(select(User).where(User.id == app.user_id))
    applicant_user = user_res.scalar_one_or_none()
    if applicant_user:
        try:
            msg = (
                f"🎉 **تبریک! درخواست استخدام شما تأیید شد.**\n\n"
                f"کد پرونده: `{app.tracking_code}`\n"
                f"موقعیت: {app.job_position}\n\n"
                "کارشناسان منابع انسانی مجموعه به زودی جهت هماهنگی مصاحبه و شروع همکاری با شما تماس خواهند گرفت."
            )
            await callback.bot.send_message(applicant_user.telegram_id, msg, parse_mode="Markdown")
        except Exception:
            pass

    await callback.message.edit_text(
        f"{callback.message.text}\n\n➖➖➖➖➖➖\n✅ **این پرونده توسط مدیر تأیید شد.**",
        reply_markup=None,
        parse_mode="Markdown"
    )
    await callback.answer("درخواست با موفقیت تأیید شد.")


@router.callback_query(F.data.startswith("adm_app_reject_"))
async def start_reject_application(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    app_id = int(callback.data.replace("adm_app_reject_", ""))
    await state.set_state(AdminReviewStates.reject_reason)
    await state.update_data(app_id=app_id)
    await callback.message.answer(
        "لطفاً **دلیل یا پیام عدم پذیرش** را برای متقاضی بنویسید (یا عدد 0 را بفرستید تا متن پیش‌فرض ارسال شود):",
        reply_markup=get_cancel_kb()
    )
    await callback.answer()


@router.message(AdminReviewStates.reject_reason, F.text)
async def finish_reject_application(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    app_id = data.get("app_id")

    app_res = await session.execute(select(JobApplication).where(JobApplication.id == app_id))
    app = app_res.scalar_one_or_none()

    reason = message.text.strip()
    if reason == "0":
        reason = "ضمن تشکر از ارسال رزومه، متأسفانه در حال حاضر امکان همکاری در این ردیف شغلی وجود ندارد."

    if app:
        app.status = "rejected"
        app.admin_notes = reason
        await session.commit()

        user_res = await session.execute(select(User).where(User.id == app.user_id))
        applicant_user = user_res.scalar_one_or_none()
        if applicant_user:
            try:
                msg = (
                    f"⚠️ **نتیجه بررسی درخواست استخدام ({app.tracking_code}):**\n\n"
                    f"پیام مدیریت:\n{reason}\n\n"
                    "اطلاعات شما در بانک استعدادهای مجموعه محفوظ بوده و در فرصت‌های آتی بررسی خواهد شد."
                )
                await message.bot.send_message(applicant_user.telegram_id, msg, parse_mode="Markdown")
            except Exception:
                pass

    await state.clear()
    await message.answer("❌ پرونده با موفقیت رد شد و پیام به متقاضی ارسال گردید.", reply_markup=get_admin_main_kb())


@router.callback_query(F.data.startswith("adm_app_needinfo_"))
async def start_needinfo_application(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    app_id = int(callback.data.replace("adm_app_needinfo_", ""))
    await state.set_state(AdminReviewStates.need_info_reason)
    await state.update_data(app_id=app_id)
    await callback.message.answer(
        "لطفاً مشخص فرمایید **چه مدارک یا اطلاعاتی دارای نقص است** تا برای متقاضی ارسال شود:",
        reply_markup=get_cancel_kb()
    )
    await callback.answer()


@router.message(AdminReviewStates.need_info_reason, F.text)
async def finish_needinfo_application(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    app_id = data.get("app_id")

    app_res = await session.execute(select(JobApplication).where(JobApplication.id == app_id))
    app = app_res.scalar_one_or_none()

    reason = message.text.strip()
    if app:
        app.status = "need_info"
        app.admin_notes = reason
        await session.commit()

        user_res = await session.execute(select(User).where(User.id == app.user_id))
        applicant_user = user_res.scalar_one_or_none()
        if applicant_user:
            try:
                msg = (
                    f"⚠️ **نقص مدارک در پرونده استخدام ({app.tracking_code})**\n\n"
                    f"توضیحات کارشناس استخدام:\n{reason}\n\n"
                    "لطفاً از طریق دکمه زیر نسبت به بارگذاری مدارک تکمیلی یا اصلاح‌شده اقدام فرمایید."
                )
                await message.bot.send_message(
                    applicant_user.telegram_id,
                    msg,
                    reply_markup=get_supplementary_doc_upload_kb(app.id),
                    parse_mode="Markdown"
                )
            except Exception:
                pass

    await state.clear()
    await message.answer("⚠️ وضعیت پرونده به «نقص مدرک» تغییر یافت و به متقاضی اطلاع‌رسانی شد.", reply_markup=get_admin_main_kb())


# ------------------ مدیریت و افزودن محصولات ------------------

@router.message(F.text == "➕ افزودن محصول جدید")
async def start_add_product(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddProductStates.code)
    await message.answer(
        "➕ **مرحله ۱ از ۹: کد محصول**\n\nلطفاً یک کد شناسه منحصر‌به‌فرد برای محصول وارد کنید (مثال: `P-101` یا `T-20`):",
        reply_markup=get_cancel_kb(),
        parse_mode="Markdown"
    )


@router.message(AddProductStates.code, F.text)
async def prod_step_code(message: Message, session: AsyncSession, state: FSMContext):
    code = message.text.strip().upper()
    existing = await session.execute(select(Product).where(Product.code == code))
    if existing.scalar_one_or_none():
        await message.answer("⚠️ محصولی با این کد قبلاً ثبت شده است. لطفاً کد دیگری وارد کنید:")
        return

    await state.update_data(code=code)
    await state.set_state(AddProductStates.title)
    await message.answer("🏷️ **مرحله ۲: عنوان و نام اثر** را وارد کنید (مثال: فرش ۶ متری دستباف تبریز):")


@router.message(AddProductStates.title, F.text)
async def prod_step_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddProductStates.category)
    await message.answer("📁 **مرحله ۳: دسته‌بندی** (مثال: فرش دستباف، تابلوفرش، گلیم، قالیچه):")


@router.message(AddProductStates.category, F.text)
async def prod_step_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text.strip())
    await state.set_state(AddProductStates.dimensions)
    await message.answer("📐 **مرحله ۴: ابعاد و اندازه** (مثال: ۲ در ۳ متر، یا ۱۲۰ در ۸۰ سانتی‌متر):")


@router.message(AddProductStates.dimensions, F.text)
async def prod_step_dimensions(message: Message, state: FSMContext):
    await state.update_data(dimensions=message.text.strip())
    await state.set_state(AddProductStates.raj_shomar)
    await message.answer("🔢 **مرحله ۵: رج‌شمار** (مثال: ۵۰ رج، ۶۰ رج اعلا):")


@router.message(AddProductStates.raj_shomar, F.text)
async def prod_step_raj(message: Message, state: FSMContext):
    await state.update_data(raj_shomar=message.text.strip())
    await state.set_state(AddProductStates.pattern_name)
    await message.answer("🎨 **مرحله ۶: نام نقشه و طرح** (مثال: لچک ترنج، خطیبی، مینیاتور فرشچیان):")


@router.message(AddProductStates.pattern_name, F.text)
async def prod_step_pattern(message: Message, state: FSMContext):
    await state.update_data(pattern_name=message.text.strip())
    await state.set_state(AddProductStates.material)
    await message.answer("🧵 **مرحله ۷: جنس الیاف و چله** (مثال: چله ابریشم، خامه مرینوس و ابریشم خالص):")


@router.message(AddProductStates.material, F.text)
async def prod_step_material(message: Message, state: FSMContext):
    await state.update_data(material=message.text.strip())
    await state.set_state(AddProductStates.price)
    await message.answer("💰 **مرحله ۸: قیمت به تومان** (فقط عدد انگلیسی یا فارسی بدون کاما، مثال: `65000000`):")


@router.message(AddProductStates.price, F.text)
async def prod_step_price(message: Message, state: FSMContext):
    raw_price = message.text.replace(",", "").replace("،", "").strip()
    # تبدیل ارقام فارسی به انگلیسی
    tr = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    clean_price = raw_price.translate(tr)

    if not clean_price.isdigit():
        await message.answer("لطفاً قیمت را فقط به صورت عدد معتبر وارد نمایید:")
        return

    await state.update_data(price=int(clean_price))
    await state.set_state(AddProductStates.marketing_pitch)
    await message.answer(
        "💡 **مرحله ۹: نکات طلایی و روش پیشنهادی بازاریابی**\n\n"
        "توضیحات جذاب و مزایای اثر را برای بازاریاب‌ها بنویسید (مثلاً: مناسب دکوراسیون کلاسیک، رنگرزی گیاهی بدون پرزدهی، ارزش سرمایه‌گذاری بالا و...):"
    )


@router.message(AddProductStates.marketing_pitch, F.text)
async def prod_step_pitch(message: Message, state: FSMContext):
    await state.update_data(marketing_pitch=message.text.strip(), photos=[])
    await state.set_state(AddProductStates.photos)
    await message.answer(
        "📸 **مرحله نهایی: ارسال تصاویر محصول**\n\n"
        "لطفاً یک یا چند عکس باکیفیت از نماهای مختلف محصول ارسال فرمایید.\n"
        "پس از پایان ارسال عکس‌ها، دکمه «✅ اتمام ارسال تصاویر و ثبت نهایی» را لمس کنید.",
        reply_markup=get_finish_product_photos_kb()
    )


@router.message(AddProductStates.photos, F.photo)
async def prod_step_photo_upload(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ تصویر شماره {len(photos)} دریافت شد.")


@router.message(AddProductStates.photos, F.text == "✅ اتمام ارسال تصاویر و ثبت نهایی")
async def finish_add_product(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])

    new_prod = Product(
        code=data.get("code"),
        title=data.get("title"),
        category=data.get("category"),
        dimensions=data.get("dimensions"),
        raj_shomar=data.get("raj_shomar"),
        pattern_name=data.get("pattern_name"),
        material=data.get("material"),
        price=data.get("price"),
        marketing_pitch=data.get("marketing_pitch"),
        is_available=True
    )
    new_prod.set_images(photos)
    session.add(new_prod)
    await session.commit()
    await state.clear()

    await message.answer(
        f"🎉 محصول **{new_prod.title}** با کد `{new_prod.code}` و {len(photos)} تصویر با موفقیت به کاتالوگ افزوده شد!",
        reply_markup=get_admin_main_kb(),
        parse_mode="Markdown"
    )


# ------------------ مدیریت موجودی محصولات ------------------

@router.message(F.text == "📦 مدیریت موجودی و محصولات")
async def manage_inventory(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    stmt = select(Product).order_by(desc(Product.id)).limit(15)
    result = await session.execute(stmt)
    products = result.scalars().all()

    if not products:
        await message.answer("محصولی یافت نشد.")
        return

    await message.answer("📦 **لیست محصولات موجود در سیستم:**")
    for prod in products:
        status_emoji = "🟢 موجود" if prod.is_available else "🔴 ناموجود"
        text = (
            f"🏷️ **{prod.title}** (کد: `{prod.code}`)\n"
            f"💰 {prod.price:,} تومان | 📐 {prod.dimensions} | {status_emoji}"
        )
        await message.answer(text, reply_markup=get_product_manage_inline_kb(prod.id, prod.is_available), parse_mode="Markdown")


@router.callback_query(F.data.startswith("toggle_prod_avail_"))
async def toggle_product_availability(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return

    prod_id = int(callback.data.replace("toggle_prod_avail_", ""))
    prod_res = await session.execute(select(Product).where(Product.id == prod_id))
    prod = prod_res.scalar_one_or_none()

    if prod:
        prod.is_available = not prod.is_available
        await session.commit()
        new_status = "موجود" if prod.is_available else "ناموجود"
        await callback.answer(f"وضعیت محصول به «{new_status}» تغییر یافت.")
        await callback.message.edit_reply_markup(reply_markup=get_product_manage_inline_kb(prod.id, prod.is_available))


@router.callback_query(F.data.startswith("del_prod_"))
async def delete_product(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return

    prod_id = int(callback.data.replace("del_prod_", ""))
    prod_res = await session.execute(select(Product).where(Product.id == prod_id))
    prod = prod_res.scalar_one_or_none()

    if prod:
        await session.delete(prod)
        await session.commit()
        await callback.message.edit_text("🗑️ این محصول با موفقیت حذف گردید.")
        await callback.answer("محصول حذف شد.")


# ------------------ آمار بازاریاب‌ها و گزارشات ------------------

@router.message(F.text == "👥 آمار بازاریاب‌ها و فروش")
async def marketers_report(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    stmt = select(Marketer).order_by(desc(Marketer.total_sales), desc(Marketer.total_referrals)).limit(10)
    result = await session.execute(stmt)
    marketers = result.scalars().all()

    total_marketers = len(marketers)
    report = (
        "👥 **گزارش عملکرد برترین بازاریابان مجموعه:**\n\n"
        f"تعداد کل بازاریابان فعال: {total_marketers}\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
    )

    if not marketers:
        report += "هنوز بازاریابی فعالیتی ثبت نکرده است."
    else:
        for i, m in enumerate(marketers, 1):
            report += (
                f"{i}. کد معرف: `{m.referral_code}` | "
                f"ورودی‌ها: {m.total_referrals} | فروش: {m.total_sales} | "
                f"پورسانت: {m.total_earnings:,} تومان\n"
            )

    await message.answer(report, reply_markup=get_admin_main_kb(), parse_mode="Markdown")


# ------------------ ارسال پیام همگانی (Broadcast) ------------------

@router.message(F.text == "📢 ارسال پیام همگانی")
async def start_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(BroadcastStates.target)
    await message.answer(
        "📢 **ارسال پیام همگانی:**\n\nلطفاً جامعه هدف دریافت‌کنندگان پیام را مشخص نمایید:",
        reply_markup=get_broadcast_target_kb()
    )


@router.callback_query(BroadcastStates.target, F.data.in_(["bc_all", "bc_marketers", "bc_applicants"]))
async def select_broadcast_target(callback: CallbackQuery, state: FSMContext):
    target = callback.data.replace("bc_", "")
    await state.update_data(target=target)
    await state.set_state(BroadcastStates.message)
    await callback.message.answer(
        "لطفاً **متن پیام همگانی** خود را ارسال فرمایید:",
        reply_markup=get_cancel_kb()
    )
    await callback.answer()


@router.callback_query(BroadcastStates.target, F.data == "bc_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("عملیات ارسال پیام همگانی لغو شد.", reply_markup=get_admin_main_kb())
    await callback.answer()


@router.message(BroadcastStates.message, F.text)
async def execute_broadcast(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    target = data.get("target")
    broadcast_text = message.text

    if target == "all":
        users_res = await session.execute(select(User.telegram_id))
    elif target == "marketers":
        users_res = await session.execute(
            select(User.telegram_id).join(Marketer, Marketer.user_id == User.id)
        )
    else:  # applicants
        users_res = await session.execute(
            select(User.telegram_id).join(JobApplication, JobApplication.user_id == User.id)
        )

    user_ids = set(users_res.scalars().all())
    sent_count = 0

    await message.answer(f"⏳ ارسال پیام برای {len(user_ids)} کاربر آغاز شد...")

    for uid in user_ids:
        try:
            await message.bot.send_message(uid, broadcast_text)
            sent_count += 1
        except Exception:
            pass

    await state.clear()
    await message.answer(
        f"✅ ارسال همگانی با موفقیت به پایان رسید.\nتعداد پیام‌های تحویل داده شده: {sent_count} از {len(user_ids)}",
        reply_markup=get_admin_main_kb()
    )
