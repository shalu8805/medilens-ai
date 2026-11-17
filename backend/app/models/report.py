from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


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

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )