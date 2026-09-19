import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from config import settings
from database.models import User, JobApplication
from keyboards.reply import (
    get_recruitment_menu,
    get_contact_request_kb,
    get_cancel_kb,
    get_finish_docs_kb,
    get_confirm_app_kb,
    get_main_menu
)
from keyboards.inline import (
    get_rules_agreement_kb,
    get_admin_app_review_kb,
    get_supplementary_doc_upload_kb
)
from utils.states import JobApplicationStates, SupplementaryDocsStates

router = Router()

RULES_AND_CONDITIONS = (
    "📜 **شرایط و قوانین عمومی استخدام در مجموعه:**\n\n"
    "۱. داشتن تابعیت جمهوری اسلامی ایران و عدم سوءپیشینه کیفری.\n"
    "۲. دارا بودن حداقل سن ۱۸ سال تمام.\n"
    "۳. تعهد به رعایت استانداردهای کیفیت، انضباط کاری و حفظ اسرار تجاری.\n"
    "۴. اولویت با افرادی است که دارای سابقه کار مرتبط در زمینه صنایع‌دستی، بافت یا فروش باشند.\n\n"
    "📂 **مدارک مورد نیاز جهت بارگذاری در ربات:**\n"
    "• تصویر صفحه اول شناسنامه یا کارت ملی\n"
    "• یک قطعه عکس پرسنلی واضح\n"
    "• نمونه‌کارهای قبلی، رزومه یا مدارک فنی‌وحرفه‌ای (در صورت وجود)\n\n"
    "⚖️ ارسال درخواست به منزله پذیرش کامل قوانین و تعهدنامه استخدام مجموعه می‌باشد."
)

@router.message(F.text == "📜 شرایط و مدارک مورد نیاز")
async def show_rules_and_requirements(message: Message):
    await message.answer(RULES_AND_CONDITIONS, reply_markup=get_recruitment_menu(), parse_mode="Markdown")


@router.message(F.text == "📝 ثبت درخواست استخدام جدید")
async def start_job_application(message: Message, session: AsyncSession, state: FSMContext):
    # بررسی وجود درخواست قبلی در انتظار
    user_res = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
    user = user_res.scalar_one_or_none()

    if user:
        pending_app = await session.execute(
            select(JobApplication).where(
                JobApplication.user_id == user.id,
                JobApplication.status.in_(["pending", "need_info"])
            )
        )
        if pending_app.scalar_one_or_none():
            await message.answer(
                "⚠️ شما در حال حاضر یک درخواست استخدام در حال بررسی یا نیازمند تکمیل مدرک دارید.\n\n"
                "جهت اطلاع از آخرین وضعیت پرونده، از گزینه «🔍 پیگیری وضعیت استخدام» استفاده کنید.",
                reply_markup=get_recruitment_menu()
            )
            return

    await state.set_state(JobApplicationStates.agree_rules)
    text = (
        "💼 **آغاز فرآیند ثبت درخواست استخدام**\n\n"
        f"{RULES_AND_CONDITIONS}\n\n"
        "آیا با شرایط و ضوابط فوق موافقت دارید؟"
    )
    await message.answer(text, reply_markup=get_rules_agreement_kb(), parse_mode="Markdown")


@router.callback_query(JobApplicationStates.agree_rules, F.data == "rules_agree")
async def process_rules_agreed(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(JobApplicationStates.full_name)
    await callback.message.answer(
        "لطفاً **نام و نام خانوادگی کامل** خود را ارسال فرمایید:",
        reply_markup=get_cancel_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(JobApplicationStates.agree_rules, F.data == "rules_decline")
async def process_rules_declined(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("فرآیند استخدام لغو شد.", reply_markup=get_recruitment_menu())
    await callback.answer()


@router.message(JobApplicationStates.full_name, F.text)
async def process_full_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 3:
        await message.answer("لطفاً یک نام و نام خانوادگی معتبر وارد کنید:")
        return
    await state.update_data(full_name=name)
    await state.set_state(JobApplicationStates.phone)
    await message.answer(
        "لطفاً **شماره تلفن همراه** خود را وارد کرده یا دکمه «📱 ارسال شماره تلفن همراه من» را لمس کنید:",
        reply_markup=get_contact_request_kb(),
        parse_mode="Markdown"
    )


@router.message(JobApplicationStates.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await state.set_state(JobApplicationStates.national_id)
    await message.answer(
        "شماره شما با موفقیت ثبت شد.\n\nلطفاً **کد ملی ۱۰ رقمی** خود را وارد فرمایید:",
        reply_markup=get_cancel_kb(),
        parse_mode="Markdown"
    )


@router.message(JobApplicationStates.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if len(phone) < 10:
        await message.answer("شماره تماس وارد شده معتبر نیست. لطفاً مجدداً وارد فرمایید:")
        return
    await state.update_data(phone=phone)
    await state.set_state(JobApplicationStates.national_id)
    await message.answer(
        "لطفاً **کد ملی ۱۰ رقمی** خود را وارد فرمایید:",
        reply_markup=get_cancel_kb(),
        parse_mode="Markdown"
    )


@router.message(JobApplicationStates.national_id, F.text)
async def process_national_id(message: Message, state: FSMContext):
    nid = message.text.strip()
    await state.update_data(national_id=nid)
    await state.set_state(JobApplicationStates.city)
    await message.answer(
        "لطفاً **نام استان و شهر محل سکونت** خود را وارد کنید:",
        reply_markup=get_cancel_kb(),
        parse_mode="Markdown"
    )


@router.message(JobApplicationStates.city, F.text)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    await state.update_data(city=city)
    await state.set_state(JobApplicationStates.age)
    await message.answer(
        "لطفاً **سن** خود را وارد کنید (مثال: ۲۸):",
        reply_markup=get_cancel_kb(),
        parse_mode="Markdown"
    )


@router.message(JobApplicationStates.age, F.text)
async def process_age(message: Message, state: FSMContext):
    age = message.text.strip()
    await state.update_data(age=age)
    await state.set_state(JobApplicationStates.job_position)
    await message.answer(
        "متقاضی چه **موقعیت شغلی یا تخصصی** هستید؟\n"
        "(مثلاً: بافنده حرفه‌ای، بازاریاب میدانی، طراح نقشه، کارشناس فروش، کنترل کیفیت و...)",
        reply_markup=get_cancel_kb(),
        parse_mode="Markdown"
    )


@router.message(JobApplicationStates.job_position, F.text)
async def process_job_position(message: Message, state: FSMContext):
    position = message.text.strip()
    await state.update_data(job_position=position)
    await state.set_state(JobApplicationStates.experience)
    await message.answer(
        "لطفاً خلاصه کوتاهی از **سوابق کاری مرتبط و مهارت‌های خود** را بنویسید:",
        reply_markup=get_cancel_kb(),
        parse_mode="Markdown"
    )


@router.message(JobApplicationStates.experience, F.text)
async def process_experience(message: Message, state: FSMContext):
    exp = message.text.strip()
    await state.update_data(experience=exp, documents=[])
    await state.set_state(JobApplicationStates.documents)
    
    instruction = (
        "📂 **مرحله بارگذاری مدارک:**\n\n"
        "لطفاً مدارک خود را شامل:\n"
        "۱. تصویر کارت ملی / شناسنامه\n"
        "۲. عکس پرسنلی\n"
        "۳. در صورت وجود، تصاویر نمونه‌کارها یا مدارک مهارتی\n\n"
        "را به صورت عکس یا فایل ارسال کنید. می‌توانید چند فایل را یکی پس از دیگری بفرستید.\n"
        "پس از اتمام ارسال، دکمه «✅ اتمام ارسال مدارک و مرحله بعد» را لمس فرمایید."
    )
    await message.answer(instruction, reply_markup=get_finish_docs_kb(), parse_mode="Markdown")


@router.message(JobApplicationStates.documents, F.photo)
async def process_document_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    docs = data.get("documents", [])
    photo_id = message.photo[-1].file_id
    docs.append({"type": "photo", "file_id": photo_id})
    await state.update_data(documents=docs)
    await message.answer(
        f"✅ مدرک شماره {len(docs)} (تصویر) دریافت شد.\n"
        "می‌توانید مدارک بیشتری بفرستید یا دکمه «اتمام ارسال مدارک» را بزنید."
    )


@router.message(JobApplicationStates.documents, F.document)
async def process_document_file(message: Message, state: FSMContext):
    data = await state.get_data()
    docs = data.get("documents", [])
    doc_id = message.document.file_id
    file_name = message.document.file_name or "فایل مدرک"
    docs.append({"type": "document", "file_id": doc_id, "file_name": file_name})
    await state.update_data(documents=docs)
    await message.answer(
        f"✅ مدرک شماره {len(docs)} ({file_name}) دریافت شد.\n"
        "می‌توانید مدارک بیشتری بفرستید یا دکمه «اتمام ارسال مدارک» را بزنید."
    )


@router.message(JobApplicationStates.documents, F.text == "✅ اتمام ارسال مدارک و مرحله بعد")
async def finish_documents(message: Message, state: FSMContext):
    data = await state.get_data()
    docs = data.get("documents", [])
    
    if not docs:
        await message.answer(
            "⚠️ لطفاً حداقل یک مدرک هویتی (تصویر کارت ملی یا شناسنامه) ارسال فرمایید.",
            reply_markup=get_finish_docs_kb()
        )
        return

    await state.set_state(JobApplicationStates.confirm)
    
    summary = (
        "📋 **پیش‌نمایش و تأیید نهایی درخواست استخدام:**\n\n"
        f"👤 **نام و نام خانوادگی:** {data.get('full_name')}\n"
        f"📱 **تلفن همراه:** {data.get('phone')}\n"
        f"🆔 **کد ملی:** {data.get('national_id')}\n"
        f"🏙️ **شهر محل سکونت:** {data.get('city')}\n"
        f"🎂 **سن:** {data.get('age')}\n"
        f"💼 **موقعیت درخواستی:** {data.get('job_position')}\n"
        f"📝 **سوابق و مهارت‌ها:** {data.get('experience')}\n"
        f"📎 **تعداد مدارک پیوست‌شده:** {len(docs)} عدد\n\n"
        "در صورت صحت اطلاعات، لطفاً دکمه «✅ تأیید نهایی و ارسال برای مدیریت» را لمس کنید."
    )
    await message.answer(summary, reply_markup=get_confirm_app_kb(), parse_mode="Markdown")


@router.message(JobApplicationStates.confirm, F.text == "✅ تأیید نهایی و ارسال برای مدیریت")
async def confirm_and_submit_application(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    user_res = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
    user = user_res.scalar_one()

    # تولید کد پیگیری یکتا
    tracking_code = f"HR-{random.randint(10000, 99999)}"

    application = JobApplication(
        user_id=user.id,
        tracking_code=tracking_code,
        full_name=data.get("full_name"),
        phone=data.get("phone"),
        national_id=data.get("national_id"),
        city=data.get("city"),
        age=data.get("age"),
        job_position=data.get("job_position"),
        experience=data.get("experience"),
        status="pending"
    )
    application.set_documents(data.get("documents", []))
    session.add(application)
    await session.commit()
    await state.clear()

    # ارسال تاییدیه به متقاضی
    success_text = (
        "🎉 **درخواست استخدام شما با موفقیت ثبت شد!**\n\n"
        f"🔑 **کد پیگیری اختصاصی شما:** `{tracking_code}`\n\n"
        "پرونده شما در صف بررسی کارشناسان استخدام قرار گرفت. "
        "به محض بررسی، نتیجه از طریق همین ربات به شما اطلاع‌رسانی خواهد شد.\n"
        "همچنین در هر زمان با استفاده از کد بالا می‌توانید وضعیت درخواست خود را استعلام نمایید."
    )
    await message.answer(success_text, reply_markup=get_recruitment_menu(), parse_mode="Markdown")

    # ارسال نوتیفیکیشن برای ادمین‌ها
    admin_alert = (
        "🔔 **یک درخواست استخدام جدید ثبت شد!**\n\n"
        f"🔑 **کد پیگیری:** `{tracking_code}`\n"
        f"👤 **نام متقاضی:** {application.full_name}\n"
        f"📱 **تلفن:** {application.phone}\n"
        f"🆔 **کدملی:** {application.national_id}\n"
        f"🏙️ **شهر:** {application.city} (سن: {application.age})\n"
        f"💼 **موقعیت شغلی:** {application.job_position}\n"
        f"📝 **سوابق:** {application.experience}\n"
        f"📂 **تعداد مدارک:** {len(application.documents)} فایل"
    )
    for admin_id in settings.admin_ids:
        try:
            await message.bot.send_message(
                admin_id,
                admin_alert,
                reply_markup=get_admin_app_review_kb(application.id),
                parse_mode="Markdown"
            )
        except Exception:
            pass


@router.message(F.text == "🔍 پیگیری وضعیت استخدام")
async def track_application_status(message: Message, session: AsyncSession):
    user_res = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
    user = user_res.scalar_one_or_none()
    
    if not user:
        await message.answer("شما هنوز درخواستی ثبت نکرده‌اید.")
        return

    stmt = select(JobApplication).where(JobApplication.user_id == user.id).order_by(desc(JobApplication.created_at))
    result = await session.execute(stmt)
    apps = result.scalars().all()

    if not apps:
        await message.answer(
            "هیچ درخواستی برای حساب کاربری شما یافت نشد. می‌توانید از طریق «📝 ثبت درخواست استخدام جدید» اقدام نمایید.",
            reply_markup=get_recruitment_menu()
        )
        return

    for app in apps:
        status_badges = {
            "pending": "⏳ در حال بررسی کارشناس",
            "approved": "✅ تأیید شده (پذیرفته در مرحله اولیه)",
            "rejected": "❌ عدم احراز شرایط / رد شده",
            "need_info": "⚠️ نیازمند مدارک یا اطلاعات تکمیلی"
        }
        status_text = status_badges.get(app.status, app.status)
        created_str = app.created_at.strftime("%Y/%m/%d - %H:%M")

        card = (
            f"📋 **پرونده استخدام:** `{app.tracking_code}`\n"
            f"💼 **موقعیت:** {app.job_position}\n"
            f"📅 **تاریخ ثبت:** {created_str}\n"
            f"📊 **وضعیت:** {status_text}\n"
        )
        if app.admin_notes:
            card += f"\n💬 **پیام مدیریت:**\n{app.admin_notes}\n"

        kb = None
        if app.status == "need_info":
            kb = get_supplementary_doc_upload_kb(app.id)

        await message.answer(card, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data.startswith("upload_supp_"))
async def start_supplementary_upload(callback: CallbackQuery, state: FSMContext):
    app_id = int(callback.data.replace("upload_supp_", ""))
    await state.set_state(SupplementaryDocsStates.documents)
    await state.update_data(app_id=app_id, documents=[])
    
    await callback.message.answer(
        "📂 **ارسال مدارک تکمیلی:**\n\n"
        "لطفاً مدارک اصلاح‌شده یا خواسته شده توسط مدیریت را به صورت عکس یا فایل ارسال کنید.\n"
        "پس از اتمام دکمه «✅ اتمام ارسال مدارک و مرحله بعد» را لمس نمایید.",
        reply_markup=get_finish_docs_kb(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(SupplementaryDocsStates.documents, F.photo)
async def process_supp_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    docs = data.get("documents", [])
    photo_id = message.photo[-1].file_id
    docs.append({"type": "photo", "file_id": photo_id})
    await state.update_data(documents=docs)
    await message.answer(f"✅ مدرک تکمیلی ({len(docs)}) دریافت شد.")


@router.message(SupplementaryDocsStates.documents, F.document)
async def process_supp_doc(message: Message, state: FSMContext):
    data = await state.get_data()
    docs = data.get("documents", [])
    doc_id = message.document.file_id
    docs.append({"type": "document", "file_id": doc_id, "file_name": message.document.file_name or "سند"})
    await state.update_data(documents=docs)
    await message.answer(f"✅ مدرک تکمیلی ({len(docs)}) دریافت شد.")


@router.message(SupplementaryDocsStates.documents, F.text == "✅ اتمام ارسال مدارک و مرحله بعد")
async def finish_supp_upload(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    app_id = data.get("app_id")
    new_docs = data.get("documents", [])

    if not new_docs:
        await message.answer("لطفاً حداقل یک مدرک ارسال کنید.", reply_markup=get_finish_docs_kb())
        return

    app_res = await session.execute(select(JobApplication).where(JobApplication.id == app_id))
    app = app_res.scalar_one_or_none()
    if app:
        existing_docs = app.documents
        existing_docs.extend(new_docs)
        app.set_documents(existing_docs)
        app.status = "pending"  # بازگشت به وضعیت در حال بررسی
        await session.commit()

        # اعلام به ادمین
        for admin_id in settings.admin_ids:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"🔔 متقاضی `{app.tracking_code}` مدارک تکمیلی خود را ارسال کرد.",
                    reply_markup=get_admin_app_review_kb(app.id),
                    parse_mode="Markdown"
                )
            except Exception:
                pass

    await state.clear()
    await message.answer(
        "✅ مدارک تکمیلی با موفقیت ثبت شد و پرونده شما مجدداً در صف بررسی کارشناس قرار گرفت.",
        reply_markup=get_recruitment_menu()
    )
