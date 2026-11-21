from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ReportRead(BaseModel):
    """API report ki ye details wapas bhejegi."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    file_type: str
    file_size: int
    category: str
    report_date: date | None
    extraction_status: str
    extraction_method: str | None
    uploaded_at: datetime