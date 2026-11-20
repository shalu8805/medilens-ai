import sys
from pathlib import Path

from app.services.report_parser import parse_report_text
from app.services.text_extraction import extract_text

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    if len(sys.argv) < 2:
        print('Use: python try_extract.py "path\\to\\file.pdf"')
        return

    path = Path(sys.argv[1])
    extension = path.suffix.lower().lstrip(".")
    file_type = "jpg" if extension == "jpeg" else extension

    text, method = extract_text(path, file_type)
    report = parse_report_text(text)

    print(f"Method      : {method}")
    print(f"Report date : {report.report_date}")
    print(f"Tests found : {len(report.values)}")
    print("-" * 78)
    print(f"{'TEST':<26}{'VALUE':>9}  {'UNIT':<12}{'REFERENCE':<18}FLAG")
    print("-" * 78)
    for v in report.values:
        print(
            f"{v.test_name:<26}{v.value:>9g}  {(v.unit or '-'):<12}"
            f"{(v.ref_text or '-'):<18}{v.reported_flag or ''}"
        )


main()