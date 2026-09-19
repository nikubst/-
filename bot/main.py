import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings
from database.session import init_db
from middlewares.db_middleware import DbSessionMiddleware
from handlers import common, recruitment, marketing, admin

# تنظیمات لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def set_default_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="شروع مجدد و منوی اصلی"),
        BotCommand(command="recruitment", description="بخش استخدام و جذب نیرو"),
        BotCommand(command="catalog", description="کاتالوگ محصولات و آثار"),
        BotCommand(command="marketer", description="پنل و کد اختصاصی بازاریاب"),
    ]
    try:
        await bot.set_my_commands(commands)
    except Exception as e:
        logger.warning(f"Could not set bot commands: {e}")

async def main():
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ":
        print("\n" + "="*50)
        print("❌ خطا: مقدار BOT_TOKEN در فایل .env تنظیم نشده است!")
        print("لطفاً فایل .env را باز کرده و توکن دریافتی از @BotFather را در متغیر BOT_TOKEN قرار دهید.")
        print("="*50 + "\n")
        sys.exit(1)

    # مقداردهی اولیه پایگاه داده
    logger.info("Initializing database schema...")
    await init_db()
    logger.info("Database initialized successfully.")

    # راه‌اندازی ربات
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # ثبت میدلور پایگاه داده
    dp.update.middleware(DbSessionMiddleware())

    # ثبت روترها
    dp.include_router(common.router)
    dp.include_router(recruitment.router)
    dp.include_router(marketing.router)
    dp.include_router(admin.router)

    # تنظیم دستورات منو
    await set_default_commands(bot)

    logger.info(f"🚀 Bot '{settings.BUSINESS_NAME}' is starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
