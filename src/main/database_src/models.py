import uuid
import os

from typing import List
from datetime import datetime

from sqlalchemy import String, Numeric, Integer, DateTime, ForeignKey, Boolean  # type: ignore[import]
from sqlalchemy.types import TypeDecorator, String
from sqlalchemy.orm import Mapped, mapped_column, relationship  # type: ignore[import]  
from sqlalchemy.dialects.postgresql import UUID # type: ignore[import]
from cryptography.fernet import Fernet
from .database import Base

# Note: load from environment variables safely
encryption_key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(encryption_key)

class EncryptedString(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        if value:
            return cipher_suite.encrypt(value.encode('utf-8')).decode('utf-8')
        return value

    def process_result_value(self, value, dialect):
        if value:
            return cipher_suite.decrypt(value.encode('utf-8')).decode('utf- 8')
        return value


class Commuter(Base):
    """
    Represents a passenger utilizing the TaxiFare platform.
    Tracks digital wallet balances and links to tranaction history.
    """
    __tablename__ = "commuters"

    # EncryptedString() to ensure POPIA compliance
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(EncryptedString(255), unique=True, nullable=False, index=True)  # E. 164 format (+27...)
    name: Mapped[str] = mapped_column(EncryptedString(255), nullable=False)
    wallet_balance: Mapped[float] = mapped_column(Numeric(precision=10, scale=2), default=0.00, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="commuter")

class Vehicle(Base):
    """
    Represents a vehicle operating on the TaxiFare platform.
    Maintains a record of trips and associated transactions.
    """
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    make: Mapped[str] = mapped_column(String(50), nullable=True)
    model: Mapped[str] = mapped_column(String(50), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="vehicle")

class Transaction(Base):
    """
    Logs financial fare exchanges executed via USSD or App channels.
    Links payment status directly back to affecetd seats and assest.
    """
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commuter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("commuters.id"), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    
    amount: Mapped[float] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Options: "MTN MoMo", "Linked Bank Account"
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False) 
    # Options: "Pending", "Completed", "Failed"
    payment_status: Mapped[str] = mapped_column(String(20), default="Pending", nullable=False, index=True)

    external_provider_reference: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    commuter: Mapped["Commuter"] = relationship("Commuter", back_populates="transactions")
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="transactions")


