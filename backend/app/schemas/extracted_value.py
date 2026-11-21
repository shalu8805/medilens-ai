from pydantic import BaseModel, ConfigDict, Field


class ExtractedValueRead(BaseModel):
    """Ek test ki value, jaisi API bahar bhejegi."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    test_name: str
    value: float
    unit: str | None
    ref_type: str | None
    ref_low: float | None
    ref_high: float | None
    ref_inclusive: bool
    ref_text: str | None
    reported_flag: str | None
    source_line: str | None
    is_corrected: bool


class ExtractedValueUpdate(BaseModel):
    """User kisi value ko sudhaarte waqt ye bhejega.

    Jo field nahi bheja jayega, wo badlega nahi.
    """

    test_name: str | None = Field(default=None, min_length=1, max_length=100)
    value: float | None = None
    unit: str | None = Field(default=None, max_length=30)
    ref_low: float | None = None
    ref_high: float | None = None
