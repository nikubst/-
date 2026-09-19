import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from database.models import User, Product, Marketer, ReferralLead
from keyboards.reply import get_marketer_menu, get_main_menu
from keyboards.inline import get_product_nav_kb

router = Router()

def format_price(amount: int) -> str:
    return f"{amount:,} تومان"


@router.message(F.text == "🔗 دریافت لینک و کد اختصاصی من")
async def get_my_referral_info(message: Message, session: AsyncSession):
    user_res = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
    user = user_res.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name or "کاربر",
            username=message.from_user.username
        )
        session.add(user)
        await session.flush()

    marketer_res = await session.execute(select(Marketer).where(Marketer.user_id == user.id))
    marketer = marketer_res.scalar_one_or_none()

    if not marketer:
        # ایجاد خودکار شناسه و کد بازاریابی
        ref_code = f"M{random.randint(1000, 9999)}"
        marketer = Marketer(
            user_id=user.id,
            referral_code=ref_code,
            commission_percent=5.0
        )
        session.add(marketer)
        await session.commit()

    bot_info = await message.bot.get_me()
    bot_username = bot_info.username
    ref_link = f"https://t.me/{bot_username}?start=ref_{marketer.referral_code}"

    text = (
        "🤝 **شناسه و لینک اختصاصی بازاریابی شما:**\n\n"
        f"🔑 **کد اختصاصی شما:** `{marketer.referral_code}`\n"
        f"🌐 **لینک اختصاصی شما:**\n`{ref_link}`\n\n"
        "💡 **نحوه عملکرد:**\n"
        "۱. این لینک را در پیج اینستاگرام، کانال، گروه یا برای مشتریان خود ارسال کنید.\n"
        "۲. هر کاربری که با این لینک وارد ربات شود، به عنوان مشتری معرفی‌شده توسط شما ثبت می‌گردد.\n"
        "۳. به ازای هر خرید موفق، **۵٪ پورسانت نقدی** بلافاصله در حساب شما ثبت و واریز خواهد شد."
    )
    await message.answer(text, reply_markup=get_marketer_menu(), parse_mode="Markdown")


@router.message(F.text == "📊 آمار و گزارش عملکرد من")
async def show_marketer_stats(message: Message, session: AsyncSession):
    user_res = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
    user = user_res.scalar_one_or_none()
    if not user:
        await message.answer("پروفایل کاربری یافت نشد.")
        return

    marketer_res = await session.execute(select(Marketer).where(Marketer.user_id == user.id))
    marketer = marketer_res.scalar_one_or_none()
    if not marketer:
        await message.answer(
            "شما هنوز پنل بازاریابی خود را فعال نکرده‌اید. لطفاً ابتدا روی «🔗 دریافت لینک و کد اختصاصی من» کلیک کنید.",
            reply_markup=get_marketer_menu()
        )
        return

    text = (
        "📊 **کارنامه و آمار فعالیت بازاریابی شما:**\n\n"
        f"🔑 **کد همکار:** `{marketer.referral_code}`\n"
        f"👥 **تعداد معرفی‌ها (ورودی جدید):** {marketer.total_referrals} نفر\n"
        f"🛒 **تعداد فروش‌های نهایی:** {marketer.total_sales} مورد\n"
        f"📈 **نرخ پورسانت:** {marketer.commission_percent}%\n"
        f"💰 **مجموع دریافتی/پورسانت:** {format_price(marketer.total_earnings)}\n\n"
        "جهت درخواست تسویه‌حساب یا ثبت سفارش مشتری، با پشتیبانی در ارتباط باشید."
    )
    await message.answer(text, reply_markup=get_marketer_menu(), parse_mode="Markdown")


@router.message(F.text.in_(["🛍️ کاتالوگ و محصولات", "📦 دریافت پکیج‌های تبلیغاتی"]))
async def browse_products(message: Message, session: AsyncSession):
    await show_product_by_index(message, session, index=0)


async def show_product_by_index(message: Message, session: AsyncSession, index: int = 0, is_edit: bool = False):
    stmt = select(Product).where(Product.is_available == True).order_by(Product.id)
    result = await session.execute(stmt)
    products = result.scalars().all()

    if not products:
        msg = "🛍️ در حال حاضر هیچ محصولی در کاتالوگ ثبت نشده است. به زودی محصولات جدید افزوده خواهد شد."
        if is_edit and isinstance(message, CallbackQuery):
            await message.message.edit_text(msg)
        else:
            await message.answer(msg)
        return

    if index < 0:
        index = 0
    if index >= len(products):
        index = len(products) - 1

    prod = products[index]
    
    caption = (
        f"🏷️ **{prod.title}** (کد: `{prod.code}`)\n\n"
        f"📁 **دسته‌بندی:** {prod.category}\n"
        f"📐 **ابعاد:** {prod.dimensions}\n"
        f"🔢 **رج‌شمار:** {prod.raj_shomar}\n"
        f"🎨 **نام طرح / نقشه:** {prod.pattern_name}\n"
        f"🧵 **جنس الیاف / چله:** {prod.material or 'ابریشم و مرینوس اعلا'}\n"
        f"💰 **قیمت:** {format_price(prod.price)}\n\n"
        f"💡 **نکات و مزایای اثر برای فروش:**\n{prod.marketing_pitch or 'اثر دستباف نفیس با رنگرزی گیاهی و بافت دقیق استادکاران مجرب.'}\n"
    )

    kb = get_product_nav_kb(
        current_index=index,
        total_count=len(products),
        product_id=prod.id
    )

    images = prod.images
    if images:
        # اگر عکس موجود باشد، با اولین عکس ارسال می‌کنیم
        if is_edit and isinstance(message, CallbackQuery):
            try:
                await message.message.delete()
            except Exception:
                pass
            await message.bot.send_photo(
                chat_id=message.from_user.id,
                photo=images[0],
                caption=caption,
                reply_markup=kb,
                parse_mode="Markdown"
            )
        else:
            await message.answer_photo(
                photo=images[0],
                caption=caption,
                reply_markup=kb,
                parse_mode="Markdown"
            )
    else:
        if is_edit and isinstance(message, CallbackQuery):
            await message.message.edit_text(caption, reply_markup=kb, parse_mode="Markdown")
        else:
            await message.answer(caption, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.startswith("prod_page_"))
async def paginate_product(callback: CallbackQuery, session: AsyncSession):
    page = int(callback.data.replace("prod_page_", ""))
    await show_product_by_index(callback, session, index=page, is_edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("prod_pkg_"))
async def send_marketing_package(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split("_")
    product_id = int(parts[2])

    prod_res = await session.execute(select(Product).where(Product.id == product_id))
    prod = prod_res.scalar_one_or_none()

    if not prod:
        await callback.answer("محصول مورد نظر یافت نشد.", show_alert=True)
        return

    # استخراج یا ایجاد کد رفرال بازاریاب
    user_res = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
    user = user_res.scalar_one_or_none()
    ref_code = "عام"
    if user:
        marketer_res = await session.execute(select(Marketer).where(Marketer.user_id == user.id))
        marketer = marketer_res.scalar_one_or_none()
        if marketer:
            ref_code = marketer.referral_code

    bot_info = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{ref_code}"

    # متن آماده جهت کپی و انتشار توسط بازاریاب
    ready_to_share_text = (
        f"✨ **معرفی اثر نفیس و اصیل: {prod.title}** ✨\n\n"
        f"🔸 ابعاد: {prod.dimensions}\n"
        f"🔸 رج‌شمار: {prod.raj_shomar}\n"
        f"🔸 نقشه و طرح: {prod.pattern_name}\n"
        f"🔸 جنس چله و خامه: {prod.material or 'ابریشم و مرینوس درجه یک'}\n\n"
        f"💎 **ویژگی‌های برجسته برای مشتری:**\n"
        f"{prod.marketing_pitch or 'رنگرزی ۱۰۰٪ سنتی و گیاهی، بافت متقارن و یکدست با درخشندگی خیره‌کننده.'}\n\n"
        f"💰 قیمت اعلامی: {format_price(prod.price)}\n\n"
        f"📦 جهت استعلام، مشاوره تخصصی و ثبت سفارش:\n"
        f"👉 {ref_link}\n"
        f"کد معرفی: {ref_code}"
    )

    await callback.message.answer(
        "📥 **پکیج آماده انتشار ویژه بازاریابان:**\n\n"
        "متن زیر و تصاویر بالا آماده فوروارد یا کپی در استوری‌ها، کانال‌ها و پیج‌های شما هستند:\n"
        "➖➖➖➖➖➖➖➖➖➖"
    )
    await callback.message.answer(ready_to_share_text)

    # ارسال عکس‌ها به صورت تک یا آلبوم بدون واترمارک/متن اضافه
    images = prod.images
    if len(images) > 1:
        media_group = [InputMediaPhoto(media=img_id) for img_id in images[:5]]
        await callback.message.answer_media_group(media=media_group)
    elif len(images) == 1:
        await callback.message.answer_photo(photo=images[0], caption="تصویر باکیفیت جهت ارائه به خریدار")

    await callback.answer("پکیج بازاریابی با موفقیت ارسال شد!")


@router.callback_query(F.data.startswith("prod_order_"))
async def handle_product_order(callback: CallbackQuery, session: AsyncSession):
    product_id = int(callback.data.replace("prod_order_", ""))
    prod_res = await session.execute(select(Product).where(Product.id == product_id))
    prod = prod_res.scalar_one_or_none()

    if not prod:
        await callback.answer("محصول یافت نشد.", show_alert=True)
        return

    # ارسال پیام اطلاع به خریدار
    msg = (
        f"🛒 **هماهنگی خرید اثر: {prod.title} (کد: {prod.code})**\n\n"
        f"قیمت: {format_price(prod.price)}\n\n"
        "جهت استعلام موجودی لحظه‌ای، مشاوره خرید و هماهنگی ارسال به سراسر کشور، "
        "کارشناس فروش آماده پاسخگویی به شماست:\n"
        "🆔 @SupportAdmin\n"
        "📞 تلفن تماس: ۰۲۱-۱۲۳۴۵۶۷۸"
    )
    await callback.message.answer(msg)

    # اطلاع به ادمین در مورد علاقه خریدار به محصول
    for admin_id in settings.admin_ids:
        try:
            await callback.bot.send_message(
                admin_id,
                f"🔔 **استعلام خرید جدید!**\n\n"
                f"👤 مشتری: {callback.from_user.full_name} (@{callback.from_user.username or 'بدون یوزرنیم'})\n"
                f"🛍️ محصول: {prod.title} (کد: `{prod.code}`)\n"
                f"💰 قیمت: {format_price(prod.price)}"
            )
        except Exception:
            pass

    await callback.answer("پیام شما به بخش فروش ارجاع داده شد.")
