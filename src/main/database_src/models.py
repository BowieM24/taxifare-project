import uuid

from typing import List
from datetime import datetime
from sqlalchemy import String, Numeric, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .database import Base

class Commuter(Base):
    """
    Represents a passenger utilizing the TaxiFare platform.
    Tracks digital wallet balances and links to tranaction history.
    """
    __tablename__ = "commuters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, nullable=False, index=True)  # E. 164 format (+27...)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
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


