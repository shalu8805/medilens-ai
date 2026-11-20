import re
from dataclasses import dataclass, field
from datetime import date, datetime

# Number jaise 11.8, 4.5, 11,800
NUMBER = r"\d[\d,]*(?:\.\d+)?"
NUMBER_RE = re.compile(rf"^{NUMBER}$")

# Reference range: "13.0 - 17.0" ya "13.0 to 17.0"
RANGE_PATTERN = rf"(?<![\d.])(?P<lo>{NUMBER})\s*(?:-|to)\s*(?P<hi>{NUMBER})"
# Limit: "< 200", ">= 40"
LIMIT_PATTERN = rf"(?P<op><=|>=|<|>)\s*(?P<limit>{NUMBER})"

# Line ke END mein reference range, aur uske baad optional flag (H/L)
REFERENCE_RE = re.compile(
    rf"(?:{RANGE_PATTERN}|{LIMIT_PATTERN})(?:\s+(?P<flag>H|L|High|Low))?\s*$",
    re.IGNORECASE,
)

# Chhoti units jinme "/" ya "%" nahi hota
KNOWN_UNITS = {
    "fl", "pg", "g", "mg", "ng", "mm", "sec", "secs", "mmhg", "iu",
    "meq", "mmol", "umol", "cells", "ratio", "gm", "u", "kg", "ml",
}

DATE_PATTERN = (
    r"(\d{1,2}[-/. ][A-Za-z]{3,9}[-/. ]\d{2,4}"
    r"|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}"
    r"|\d{4}-\d{2}-\d{2})"
)
REPORT_DATE_RE = re.compile(
    rf"report(?:ed)?\s*date\s*[:\-]?\s*{DATE_PATTERN}", re.IGNORECASE
)
OTHER_DATE_RE = re.compile(
    rf"(?:collect\w*|sample|registered|date)\s*(?:date)?\s*[:\-]?\s*{DATE_PATTERN}",
    re.IGNORECASE,
)
DATE_FORMATS = [
    "%d-%b-%Y", "%d %b %Y", "%d/%b/%Y", "%d.%b.%Y",
    "%d-%B-%Y", "%d %B %Y", "%d/%B/%Y",
    "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
    "%d-%m-%y", "%d/%m/%y", "%Y-%m-%d",
]


@dataclass
class ParsedValue:
    test_name: str
    value: float
    unit: str | None
    ref_type: str | None  # "range", "upper_limit", "lower_limit" ya None
    ref_low: float | None
    ref_high: float | None
    ref_inclusive: bool
    ref_text: str | None
    reported_flag: str | None  # report mein chhapa H/L (sirf cross-check ke liye)
    raw_line: str


@dataclass
class ParsedReport:
    report_date: date | None = None
    values: list[ParsedValue] = field(default_factory=list)


def _to_float(token: str) -> float:
    return float(token.replace(",", ""))


def _normalize(line: str) -> str:
    # Alag alag tarah ke dash ko "-" bana do, spaces saaf karo
    for dash in ("\u2013", "\u2014", "\u2212"):
        line = line.replace(dash, "-")
    return " ".join(line.split())


def _is_unit(token: str) -> bool:
    lowered = token.lower()
    return "/" in lowered or "%" in lowered or lowered in KNOWN_UNITS


def _split_prefix(prefix: str):
    """'Hemoglobin 11.8 g/dL' ko (naam ke tokens, value, unit) mein todta hai."""
    tokens = prefix.split()
    for unit_len in (1, 2):
        if len(tokens) > unit_len:
            unit = " ".join(tokens[-unit_len:])
            value_token = tokens[-unit_len - 1]
            name_tokens = tokens[: -unit_len - 1]
            if (
                name_tokens
                and NUMBER_RE.match(value_token)
                and _is_unit(unit.replace(" ", ""))
            ):
                return name_tokens, value_token, unit
    return None


def _clean_name(name: str) -> str | None:
    name = name.strip(" :-.,;|")
    if not name or len(name) > 80 or not re.search(r"[A-Za-z]", name):
        return None
    return name


def parse_line(line: str) -> ParsedValue | None:
    """Ek line se ek test ki value nikalta hai. Na samajh aaye to None."""
    line = _normalize(line)
    if not line:
        return None

    match = REFERENCE_RE.search(line)
    prefix = line[: match.start()].strip() if match else line

    parts = _split_prefix(prefix)
    if parts is None and match:
        # Unit nahi mili, par range hai: aakhri number ko value maano
        tokens = prefix.split()
        if len(tokens) >= 2 and NUMBER_RE.match(tokens[-1]):
            parts = (tokens[:-1], tokens[-1], None)
    if parts is None:
        return None

    name_tokens, value_token, unit = parts
    name = _clean_name(" ".join(name_tokens))
    if name is None:
        return None

    ref_type = ref_low = ref_high = ref_text = reported_flag = None
    ref_inclusive = True

    if match:
        ref_text = line[match.start(): match.end()].strip()
        if match.group("flag"):
            reported_flag = match.group("flag")[0].upper()
            ref_text = ref_text[: -len(match.group("flag"))].strip()

        if match.group("lo") is not None:
            low, high = _to_float(match.group("lo")), _to_float(match.group("hi"))
            # Ulta range (low > high) bharosemand nahi: classify nahi karenge
            if low <= high:
                ref_type, ref_low, ref_high = "range", low, high
        else:
            limit = _to_float(match.group("limit"))
            operator = match.group("op")
            ref_inclusive = operator in ("<=", ">=")
            if operator.startswith("<"):
                ref_type, ref_high = "upper_limit", limit
            else:
                ref_type, ref_low = "lower_limit", limit

    return ParsedValue(
        test_name=name,
        value=_to_float(value_token),
        unit=unit,
        ref_type=ref_type,
        ref_low=ref_low,
        ref_high=ref_high,
        ref_inclusive=ref_inclusive,
        ref_text=ref_text,
        reported_flag=reported_flag,
        raw_line=line,
    )


def _parse_date(text: str) -> date | None:
    text = " ".join(text.split())
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def find_report_date(text: str) -> date | None:
    """'Report Date: ...' dhundta hai. Na mile to collection/sample date."""
    for pattern in (REPORT_DATE_RE, OTHER_DATE_RE):
        found = pattern.search(text)
        if found:
            parsed = _parse_date(found.group(1))
            if parsed:
                return parsed
    return None


def parse_report_text(text: str) -> ParsedReport:
    report = ParsedReport(report_date=find_report_date(text))
    for line in text.splitlines():
        parsed = parse_line(line)
        if parsed is not None:
            report.values.append(parsed)
    return report