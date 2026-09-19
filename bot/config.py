import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_database.db")
    BUSINESS_NAME: str = os.getenv("BUSINESS_NAME", "قالیار | سامانه جامع فرش و هنر")
    
    @property
    def admin_ids(self) -> List[int]:
        raw = os.getenv("ADMIN_IDS", "")
        if not raw:
            return []
        ids = []
        for item in raw.split(","):
            item = item.strip()
            if item.isdigit():
                ids.append(int(item))
        return ids

settings = Settings()
