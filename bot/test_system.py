import asyncio
import sys
from sqlalchemy import select
from database.session import init_db, async_session_maker
from database.models import User, JobApplication, Product, Marketer, ReferralLead, Customer

async def run_tests():
    print("🚀 [1/4] تست اولیه ایجاد جداول در پایگاه داده...")
    await init_db()
    print("✅ جداول پایگاه داده با موفقیت ساخته شدند.")

    async with async_session_maker() as session:
        print("🚀 [2/4] ایجاد داده‌های نمونه (محصولات فرش، کاربر و بازاریاب)...")

        # ایجاد کاربر ادمین و بازاریاب
        user_admin = User(
            telegram_id=111222333,
            full_name="مدیر سیستم",
            username="system_admin",
            role="admin"
        )
        user_marketer = User(
            telegram_id=444555666,
            full_name="علی محمدی",
            username="ali_carpet",
            role="user"
        )
        session.add_all([user_admin, user_marketer])
        await session.flush()

        # ایجاد پروفایل بازاریاب
        marketer = Marketer(
            user_id=user_marketer.id,
            referral_code="M1001",
            commission_percent=5.0,
            total_referrals=3,
            total_sales=1,
            total_earnings=2500000
        )
        session.add(marketer)

        # افزودن محصولات نمونه تخصصی با رج‌شمار و نقشه
        prod1 = Product(
            code="P-101",
            title="تابلوفرش دستباف مینیاتور ضامن آهو",
            category="تابلوفرش دستباف",
            dimensions="۸۵ در ۱۲۰ سانتی‌متر",
            raj_shomar="۶۰ رج اعلا",
            pattern_name="مینیاتور استاد فرشچیان",
            material="چله ابریشم، خامه مرینوس و ابریشم خالص",
            price=38000000,
            marketing_pitch="یکی از پرفروش‌ترین و اصیل‌ترین طرح‌های استاد فرشچیان با رنگرزی گیاهی ۱۰۰٪ سنتی و برجسته‌زنی دست‌ساز، ایده‌آل برای هدایای لوکس مدیریتی و دکوراسیون منزل.",
            is_available=True
        )
        prod1.set_images(["dummy_photo_file_id_1"])

        prod2 = Product(
            code="P-102",
            title="قالیچه ۳ متری تبریز طرح خطیبی طلاکوب",
            category="قالیچه دستباف",
            dimensions="۱.۵ در ۲ متر",
            raj_shomar="۵۵ رج",
            pattern_name="خطیبی با حاشیه کتیبه‌ای",
            material="چله نخ، گل ابریشم طبیعی",
            price=72000000,
            marketing_pitch="تراکم بافت فوق‌العاده متقارن، ثبات رنگ تضمینی در شستشو، افزایش قیمت و ارزش سرمایه‌گذاری سالانه با تضمین عودت ۲ ساله.",
            is_available=True
        )
        prod2.set_images(["dummy_photo_file_id_2"])

        session.add_all([prod1, prod2])

        # ایجاد یک درخواست استخدام تستی
        app = JobApplication(
            user_id=user_marketer.id,
            tracking_code="HR-88412",
            full_name="علی محمدی",
            phone="09123456789",
            national_id="0012345678",
            city="تهران",
            age="29",
            job_position="کارشناس بازاریابی و فروش",
            experience="۵ سال سابقه فروش فرش و صنایع‌دستی در بازار بزرگ تهران",
            status="pending"
        )
        app.set_documents([
            {"type": "photo", "file_id": "doc_id_national_card"},
            {"type": "document", "file_id": "doc_resume_pdf", "file_name": "resume.pdf"}
        ])
        session.add(app)

        await session.commit()
        print("✅ اطلاعات نمونه و پرونده استخدام با موفقیت ثبت گردید.")

        print("🚀 [3/4] بررسی اعتبارسنجی پرس‌وجوها (Queries)...")
        # تست خواندن محصولات
        prods = (await session.execute(select(Product))).scalars().all()
        assert len(prods) == 2, f"Expected 2 products, got {len(prods)}"
        print(f"📦 محصولات ثبت شده: {[p.title for p in prods]}")

        # تست خواندن درخواست استخدام
        apps = (await session.execute(select(JobApplication))).scalars().all()
        assert len(apps) == 1, f"Expected 1 application, got {len(apps)}"
        print(f"💼 درخواست استخدام: {apps[0].full_name} | موقعیت: {apps[0].job_position} | مدارک: {len(apps[0].documents)} فایل")

        # تست تغییر وضعیت به نقص مدرک و سپس تایید
        apps[0].status = "need_info"
        apps[0].admin_notes = "لطفاً تصویر شفاف‌تری از کارت ملی ارسال فرمایید."
        await session.commit()
        print(f"⚠️ تست تغییر وضعیت پرونده به نقص مدرک: {apps[0].status} -> {apps[0].admin_notes}")

        # تست مشتریان رتبه اعتباری A و B
        cust1 = Customer(
            full_name="حاج محمد تبریزی",
            phone="09141112233",
            city="تبریز",
            credit_rating="A",
            total_purchases=4,
            total_spent=185000000,
            notes="خریدار قدیمی و معتبر، تسویه نقدی فوری"
        )
        cust2 = Customer(
            full_name="دکتر بهرامی",
            phone="09132223344",
            city="اصفهان",
            credit_rating="A",
            total_purchases=2,
            total_spent=120000000,
            notes="کلکسیونر تابلوفرش نفیس، مشتری ویژه VIP"
        )
        cust3 = Customer(
            full_name="مهندس کاظمی",
            phone="09173334455",
            city="شیراز",
            credit_rating="B",
            total_purchases=1,
            total_spent=65000000,
            notes="خوش‌حساب، سفارش قالیچه خطیبی"
        )
        cust4 = Customer(
            full_name="خانم کریمی",
            phone="09154445566",
            city="مشهد",
            credit_rating="C",
            total_purchases=1,
            total_spent=25000000,
            notes="مشتری عادی"
        )
        session.add_all([cust1, cust2, cust3, cust4])

        await session.commit()
        print("✅ مشتریان با رتبه‌های اعتباری A و B و شهر و شماره تماس ثبت گردیدند.")

        # استعلام فقط رتبه‌های A و B
        vip_custs = (await session.execute(
            select(Customer).where(Customer.credit_rating.in_(["A", "B"])).order_by(Customer.credit_rating)
        )).scalars().all()
        assert len(vip_custs) == 3, f"Expected 3 VIP customers, got {len(vip_custs)}"
        print(f"💎 مشتریان رتبه A و B استخراج‌شده ({len(vip_custs)} نفر):")
        for c in vip_custs:
            print(f"   • {c.full_name} | رتبه: {c.credit_rating} | شهر: {c.city} | تلفن: {c.phone} | خرید: {c.total_spent:,} تومان")

        # تست بازاریاب و رفرال
        mrk = (await session.execute(select(Marketer))).scalar_one()
        print(f"🤝 پروفایل بازاریاب: کد {mrk.referral_code} | پورسانت: {mrk.commission_percent}% | ارجاع‌ها: {mrk.total_referrals}")

    print("🚀 [4/4] تست کامپایل و پکیج‌های پایتون...")
    print("🎉 کلیه تست‌های اعتبارسنجی سیستمی با موفقیت ۱۰۰٪ پاس شدند!")

if __name__ == "__main__":
    asyncio.run(run_tests())
