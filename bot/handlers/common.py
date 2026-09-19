from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from database.models import User, Marketer, ReferralLead
from keyboards.reply import get_main_menu, get_recruitment_menu, get_marketer_menu
from keyboards.admin_kb import get_admin_main_kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name or "کاربر گرامی"
    username = message.from_user.username

    # بررسی یا ایجاد کاربر
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        role = "admin" if telegram_id in settings.admin_ids else "user"
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            role=role
        )
        session.add(user)
        await session.flush()
    else:
        # بروزرسانی نقش در صورت اضافه شدن به لیست ادمین‌ها
        if telegram_id in settings.admin_ids and user.role != "admin":
            user.role = "admin"

    # بررسی رفرال کد دیپ‌لینک (مثلاً /start ref_M1234)
    args = message.text.split()[1:]
    if args and args[0].startswith("ref_"):
        ref_code = args[0].replace("ref_", "").strip()
        marketer_stmt = select(Marketer).where(Marketer.referral_code == ref_code)
        marketer_res = await session.execute(marketer_stmt)
        marketer = marketer_res.scalar_one_or_none()
        
        if marketer and marketer.user_id != user.id:
            lead_check = await session.execute(
                select(ReferralLead).where(
                    ReferralLead.marketer_id == marketer.id,
                    ReferralLead.customer_telegram_id == telegram_id
                )
            )
            if not lead_check.scalar_one_or_none():
                new_lead = ReferralLead(marketer_id=marketer.id, customer_telegram_id=telegram_id)
                session.add(new_lead)
                marketer.total_referrals += 1

    is_admin = telegram_id in settings.admin_ids
    welcome_text = (
        f"سلام {full_name} عزیز، به ربات رسمی **{settings.BUSINESS_NAME}** خوش آمدید 🌹\n\n"
        "ما فرآیندهای کسب‌وکارمان را برای شما هوشمند و خودکار کرده‌ایم:\n\n"
        "💼 **بخش استخدام:** ثبت درخواست همکاری، بارگذاری مدارک و رهگیری آنلاین وضعیت استخدام\n"
        "🛍️ **کاتالوگ محصولات:** مشاهده آثار نفیس به همراه ابعاد، رج‌شمار، طرح و نقشه\n"
        "🤝 **بخش همکاران و بازاریابی:** دریافت کد و لینک اختصاصی، دریافت فایل‌های فروش و کسب پورسانت\n\n"
        "لطفاً از منوی زیر بخش مورد نظر خود را انتخاب فرمایید:"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu(is_admin=is_admin), parse_mode="Markdown")


@router.message(F.text == "🔙 بازگشت به منوی اصلی")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    is_admin = message.from_user.id in settings.admin_ids
    await message.answer("به منوی اصلی بازگشتید:", reply_markup=get_main_menu(is_admin=is_admin))


@router.message(F.text == "❌ انصراف و بازگشت")
async def cancel_operation(message: Message, state: FSMContext):
    await state.clear()
    is_admin = message.from_user.id in settings.admin_ids
    await message.answer("عملیات لغو شد. به منوی اصلی بازگشتید.", reply_markup=get_main_menu(is_admin=is_admin))


@router.message(F.text == "💼 بخش استخدام و جذب نیرو")
async def open_recruitment_menu(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "💼 **بخش استخدام و جذب نیرو**\n\n"
        "در این بخش می‌توانید شرایط و مدارک استخدام را مشاهده نموده، "
        "درخواست خود را ثبت کرده و وضعیت پرونده خود را پیگیری کنید.\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    await message.answer(text, reply_markup=get_recruitment_menu(), parse_mode="Markdown")


@router.message(F.text == "🤝 پنل و کد اختصاصی بازاریاب")
async def open_marketer_menu(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "🤝 **پنل همکاری در فروش و بازاریابی**\n\n"
        "با دریافت کد و لینک اختصاصی خود، می‌توانید محصولات مجموعه را معرفی کنید "
        "و به ازای هر مشتری یا فروش موفق، پورسانت نقدی دریافت کنید.\n\n"
        "از گزینه‌های زیر استفاده نمایید:"
    )
    await message.answer(text, reply_markup=get_marketer_menu(), parse_mode="Markdown")


@router.message(F.text == "📞 پشتیبانی و تماس")
async def support_info(message: Message):
    text = (
        f"📞 **ارتباط با واحد مدیریت و پشتیبانی {settings.BUSINESS_NAME}**\n\n"
        "🔹 ساعت پاسخگویی: شنبه تا چهارشنبه، ساعت ۹ الی ۱۸\n"
        "🔹 پشتیبانی آنلاین تلگرام: @SupportAdmin\n"
        "🔹 شماره تماس: ۰۲۱-۱۲۳۴۵۶۷۸\n\n"
        "در صورت وجود هرگونه سؤال، کارشناسان ما آماده راهنمایی شما هستند."
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "⚙️ پنل مدیریت")
async def open_admin_panel(message: Message, state: FSMContext):
    await state.clear()
    if message.from_user.id not in settings.admin_ids:
        await message.answer("⛔ شما به این بخش دسترسی ندارید.")
        return
    
    text = (
        "⚙️ **پنل مدیریت ربات**\n\n"
        "از این بخش می‌توانید درخواست‌های استخدام را بررسی نموده، "
        "محصول جدید با جزئیات کامل ثبت کنید، وضعیت موجودی را تغییر دهید "
        "و گزارش عملکرد بازاریاب‌ها را مشاهده فرمایید."
    )
    await message.answer(text, reply_markup=get_admin_main_kb(), parse_mode="Markdown")
