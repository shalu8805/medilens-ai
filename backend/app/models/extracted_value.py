from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.report import Report


class ExtractedValue(Base):
    """Report ki ek row: ek test ki value, unit aur reference range."""

    __tablename__ = "extracted_values"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )

    test_name: Mapped[str] = mapped_column(String(100))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Reference range: "range", "upper_limit", "lower_limit" ya None
    ref_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ref_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    ref_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    ref_inclusive: Mapped[bool] = mapped_column(Boolean, default=True)
    ref_text: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # Report mein chhapa H/L (sirf cross-check ke liye)
    reported_flag: Mapped[str | None] = mapped_column(String(1), nullable=True)

    # Report ki asli line (user ko dikhane ke liye, taaki wo sudhaar sake)
    source_line: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Kya user ne ise haath se sudhaara hai
    is_corrected: Mapped[bool] = mapped_column(Boolean, default=False)

    report: Mapped["Report"] = relationship(back_populates="values")