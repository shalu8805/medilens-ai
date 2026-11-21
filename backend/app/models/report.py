
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.extracted_value import ExtractedValue


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Ye report kis user ki hai
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # User ne jo naam diya tha (sirf dikhane ke liye)
    original_filename: Mapped[str] = mapped_column(String(255))
    # Disk par asli naam: random, taaki koi guess na kar sake
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True)

    file_type: Mapped[str] = mapped_column(String(10))  # pdf, jpg, png
    file_size: Mapped[int] = mapped_column(Integer)  # bytes mein

    # History page ke filters ke liye
    category: Mapped[str] = mapped_column(String(50), default="Other")
    report_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Text extraction ki sthiti: pending / done / failed
    extraction_status: Mapped[str] = mapped_column(String(20), default="pending")
    # Text kaise nikla: digital_pdf / ocr / mixed
    extraction_method: Mapped[str | None] = mapped_column(String(20), nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Is report ki extracted values. Report delete hone par ye bhi delete honge
    values: Mapped[list["ExtractedValue"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )
    