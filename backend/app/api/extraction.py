from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.extracted_value import ExtractedValue
from app.models.report import Report
from app.models.user import User
from app.schemas.extracted_value import ExtractedValueRead, ExtractedValueUpdate
from app.schemas.report import ReportRead
from app.services.extraction_service import run_extraction

router = APIRouter(prefix="/reports", tags=["Extraction"])


def _get_user_report(db: Session, report_id: int, user: User) -> Report:
    """Sirf us user ki apni report. Doosre ki ho to 404."""
    report = db.scalar(
        select(Report).where(Report.id == report_id, Report.user_id == user.id)
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )
    return report


def _get_value(db: Session, report: Report, value_id: int) -> ExtractedValue:
    value = db.scalar(
        select(ExtractedValue).where(
            ExtractedValue.id == value_id,
            ExtractedValue.report_id == report.id,
        )
    )
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Value not found"
        )
    return value


@router.post("/{report_id}/extract", response_model=ReportRead)
def extract_report(
    report_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = _get_user_report(db, report_id, current_user)

    # Pehle se nikli hui values (aur user ke sudhaar) galti se mit na jayein
    if report.extraction_status == "done" and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already extracted. Use force=true to redo (your corrections will be lost).",
        )

    return run_extraction(db, report)


@router.get("/{report_id}/values", response_model=list[ExtractedValueRead])
def list_values(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = _get_user_report(db, report_id, current_user)
    return db.scalars(
        select(ExtractedValue)
        .where(ExtractedValue.report_id == report.id)
        .order_by(ExtractedValue.id)
    ).all()


@router.patch("/{report_id}/values/{value_id}", response_model=ExtractedValueRead)
def correct_value(
    report_id: int,
    value_id: int,
    update: ExtractedValueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = _get_user_report(db, report_id, current_user)
    item = _get_value(db, report, value_id)

    # Sirf wahi fields jo user ne bheje
    changes = update.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No changes sent"
        )
    if changes.get("test_name", "x") is None or changes.get("value", 0) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="test_name and value cannot be empty",
        )

    for field, new_value in changes.items():
        setattr(item, field, new_value)

    # Reference range badli ho to uska type aur text dobara banao
    if "ref_low" in changes or "ref_high" in changes:
        low, high = item.ref_low, item.ref_high
        if low is not None and high is not None:
            if low > high:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ref_low cannot be greater than ref_high",
                )
            item.ref_type, item.ref_text = "range", f"{low:g} - {high:g}"
        elif high is not None:
            item.ref_type, item.ref_text = "upper_limit", f"< {high:g}"
        elif low is not None:
            item.ref_type, item.ref_text = "lower_limit", f"> {low:g}"
        else:
            item.ref_type, item.ref_text = None, None
        item.ref_inclusive = True

    item.is_corrected = True
    db.commit()
    db.refresh(item)
    return item


@router.delete(
    "/{report_id}/values/{value_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_value(
    report_id: int,
    value_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = _get_user_report(db, report_id, current_user)
    item = _get_value(db, report, value_id)
    db.delete(item)
    db.commit()