from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str] = mapped_column(String(30), nullable=False)

    # CRITICAL: This MUST be unique. It's our invariant for the Upsert mechanism.
    link: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Composite Indices for High-Load Search Queries (Time O(log N))
    __table_args__ = (
        Index("ix_cars_brand_model", "brand", "model"),
        Index("ix_cars_price_year", "price", "year"),
    )