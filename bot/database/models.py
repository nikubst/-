from datetime import datetime
import json
from typing import List, Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
    role = Column(String(50), default="user")  # 'user', 'marketer', 'admin'
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")
    marketer_profile = relationship("Marketer", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.telegram_id} - {self.full_name}>"


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tracking_code = Column(String(50), unique=True, index=True, nullable=False)
    
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    national_id = Column(String(50), nullable=True)
    city = Column(String(100), nullable=False)
    age = Column(String(20), nullable=True)
    job_position = Column(String(100), nullable=False)
    experience = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    
    # Store list of Telegram file_ids and types as JSON
    documents_json = Column(Text, default="[]")
    
    # pending, approved, rejected, need_info
    status = Column(String(50), default="pending", index=True)
    admin_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="applications")

    @property
    def documents(self) -> List[dict]:
        try:
            return json.loads(self.documents_json or "[]")
        except Exception:
            return []

    def set_documents(self, docs: List[dict]):
        self.documents_json = json.dumps(docs, ensure_ascii=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, default="فرش و تابلوفرش")
    
    # فرش/صنایع دستی مشخصات اختصاصی
    dimensions = Column(String(100), nullable=False)      # ابعاد
    raj_shomar = Column(String(50), nullable=False)       # رج‌شمار
    pattern_name = Column(String(100), nullable=False)     # نام نقشه یا طرح
    material = Column(String(150), nullable=True)         # جنس چله و ابریشم
    price = Column(BigInteger, nullable=False)            # قیمت (تومان)
    
    # متون و سناریوی پیشنهادی بازاریابی
    marketing_pitch = Column(Text, nullable=True)
    
    # عکس‌ها در تلگرام (لیست file_id به صورت JSON)
    images_json = Column(Text, default="[]")
    
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def images(self) -> List[str]:
        try:
            return json.loads(self.images_json or "[]")
        except Exception:
            return []

    def set_images(self, imgs: List[str]):
        self.images_json = json.dumps(imgs, ensure_ascii=False)


class Marketer(Base):
    __tablename__ = "marketers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    referral_code = Column(String(50), unique=True, index=True, nullable=False)
    commission_percent = Column(Float, default=5.0)  # درصد کمیسیون پیش‌فرض
    
    total_referrals = Column(Integer, default=0)
    total_sales = Column(Integer, default=0)
    total_earnings = Column(BigInteger, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="marketer_profile")
    leads = relationship("ReferralLead", back_populates="marketer", cascade="all, delete-orphan")


class ReferralLead(Base):
    __tablename__ = "referral_leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    marketer_id = Column(Integer, ForeignKey("marketers.id"), nullable=False)
    customer_telegram_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    marketer = relationship("Marketer", back_populates="leads")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=True, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True)
    
    # رتبه اعتباری: A (عالی/خوش‌حساب)، B (خوب)، C (متوسط)، D (نیازمند بررسی)
    credit_rating = Column(String(10), nullable=False, default="B", index=True)
    
    total_purchases = Column(Integer, default=1)
    total_spent = Column(BigInteger, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Customer {self.full_name} - {self.city} - Rating: {self.credit_rating}>"
