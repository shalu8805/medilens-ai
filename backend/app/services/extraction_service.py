from sqlalchemy.orm import Session

from app.models.extracted_value import ExtractedValue
from app.models.report import Report
from app.services.file_storage import STORAGE_ROOT
from app.services.report_parser import parse_report_text
from app.services.text_extraction import extract_text


def run_extraction(db: Session, report: Report) -> Report:
    """Report ki file padhke values nikaalta hai aur database mein save karta hai."""
    file_path = STORAGE_ROOT / str(report.user_id) / report.stored_filename

    try:
        if not file_path.exists():
            raise FileNotFoundError("Report file missing on disk")
        text, method = extract_text(file_path, report.file_type)
        parsed = parse_report_text(text)
    except Exception:
        # Medical data private hai: error ke saath report ka content log nahi karte,
        # sirf status 'failed' rakhte hain.
        report.extraction_status = "failed"
        db.commit()
        db.refresh(report)
        return report

    # Purani values hatao (delete-orphan se database se bhi hat jati hain)
    report.values.clear()

    for item in parsed.values:
        report.values.append(
            ExtractedValue(
                test_name=item.test_name[:100],
                value=item.value,
                unit=item.unit[:30] if item.unit else None,
                ref_type=item.ref_type,
                ref_low=item.ref_low,
                ref_high=item.ref_high,
                ref_inclusive=item.ref_inclusive,
                ref_text=item.ref_text[:60] if item.ref_text else None,
                reported_flag=item.reported_flag,
                source_line=item.raw_line[:255],
            )
        )

    # User ne date nahi di thi, par report mein mili, to wo bhar do
    if report.report_date is None and parsed.report_date is not None:
        report.report_date = parsed.report_date

    report.extraction_status = "done"
    report.extraction_method = method

    db.commit()
    db.refresh(report)
    return report