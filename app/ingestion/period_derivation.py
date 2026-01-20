from datetime import date, datetime
import calendar


from datetime import date
import calendar

# app/ingestion/period_derivation.py

from datetime import date, timedelta
import calendar

# ------------------------------------------------------------
# Month normalization map (single source of truth)
# ------------------------------------------------------------
MONTH_NAME_TO_INDEX = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}
from datetime import date, datetime


def extract_calendar_month(value) -> int:
    """
    Extract calendar month (1–12) from:
    - date / datetime
    - ISO date string (YYYY-MM-DD)
    - strings like 'Apr-2024', 'April 2024', 'Apr'
    """

    # Case 1: date / datetime
    if isinstance(value, (date, datetime)):
        return value.month

    # Case 2: string
    if isinstance(value, str):
        v = value.strip()

        # Try ISO date
        try:
            dt = datetime.fromisoformat(v)
            return dt.month
        except ValueError:
            pass

        # Try month name
        key = v.lower().split()[0]
        if key in MONTH_NAME_TO_INDEX:
            return MONTH_NAME_TO_INDEX[key]

        # Try 'Apr-2024'
        parts = v.replace("-", " ").split()
        for p in parts:
            if p.lower() in MONTH_NAME_TO_INDEX:
                return MONTH_NAME_TO_INDEX[p.lower()]

    raise ValueError(f"Cannot extract month from value: {value}")


def normalize_month(value) -> int:
    """
    Accepts:
    - int (1–12)
    - str month name ("Apr", "April")

    Returns:
    - month index (1–12)
    """
    if value is None:
        raise ValueError("Month value is required for monthly data")

    if isinstance(value, int):
        if 1 <= value <= 12:
            return value
        raise ValueError("Month index must be between 1 and 12")

    if isinstance(value, str):
        key = value.strip().lower()
        if key in MONTH_NAME_TO_INDEX:
            return MONTH_NAME_TO_INDEX[key]

    raise ValueError(f"Unsupported month value: {value}")


def derive_period_dates(
    period_type: str,
    fiscal_year: int,
    fiscal_quarter: int | None,
    fiscal_month: int | None,
    fiscal_year_start_month: int,
):
    """
    Deterministically derive period_start and period_end.

    Supported:
    - month
    - quarter
    - year
    """

    # ------------------------
    # MONTHLY
    # ------------------------
    if period_type == "month":
        if fiscal_month is None:
            raise ValueError("fiscal_month is required for monthly data")

        month = normalize_month(fiscal_month)

        year_offset = 1 if month < fiscal_year_start_month else 0
        calendar_year = fiscal_year - year_offset

        period_start = date(calendar_year, month, 1)
        period_end = date(
            calendar_year,
            month,
            calendar.monthrange(calendar_year, month)[1],
        )

        return period_start, period_end


    # ------------------------
    # QUARTERLY
    # ------------------------
    if period_type == "quarter":
        if fiscal_quarter is None:
            raise ValueError("Quarter required for quarterly data")

        start_month = (
            (fiscal_year_start_month - 1) + (fiscal_quarter - 1) * 3
        ) % 12 + 1

        start_year = (
            fiscal_year
            if start_month >= fiscal_year_start_month
            else fiscal_year + 1
        )

        period_start = date(start_year, start_month, 1)

        end_month = (start_month + 2 - 1) % 12 + 1
        end_year = start_year if end_month >= start_month else start_year + 1

        period_end = date(
            end_year,
            end_month,
            calendar.monthrange(end_year, end_month)[1],
        )

        return period_start, period_end

    # ------------------------
    # YEARLY
    # ------------------------
    if period_type == "year":
        start_year = fiscal_year
        start_month = fiscal_year_start_month

        period_start = date(start_year, start_month, 1)

        end_year = start_year + 1 if start_month > 1 else start_year
        end_month = start_month - 1 if start_month > 1 else 12

        period_end = date(
            end_year,
            end_month,
            calendar.monthrange(end_year, end_month)[1],
        )

        return period_start, period_end

    # ------------------------
    # UNSUPPORTED
    # ------------------------
    raise ValueError(f"Unsupported period_type: {period_type}")



def parse_fiscal_year(value) -> int:
    """
    Accepts:
    - FY2024
    - 2024
    - "2024"
    Returns:
    - 2024
    """
    if value is None:
        raise ValueError("Fiscal year is required")

    if isinstance(value, int):
        return value

    value = str(value).strip().upper()

    if value.startswith("FY"):
        return int(value.replace("FY", ""))

    return int(value)



def derive_fiscal_year_from_date(
    value,
    fiscal_year_start_month: int,
) -> int:
    """
    Deterministically derive fiscal year from a date-like value.

    Accepts:
    - datetime.date
    - datetime.datetime
    - ISO date string (YYYY-MM-DD)
    - strings like 'Apr-2024', 'April 2024'

    Returns:
    - fiscal_year (int)

    Raises:
    - ValueError if derivation is impossible
    """

    calendar_year = None
    calendar_month = None

    # -----------------------------
    # Case 1: date / datetime object
    # -----------------------------
    if isinstance(value, (date, datetime)):
        calendar_year = value.year
        calendar_month = value.month

    # -----------------------------
    # Case 2: string input
    # -----------------------------
    elif isinstance(value, str):
        v = value.strip()

        # Try ISO format first
        try:
            dt = datetime.fromisoformat(v)
            print("DEBUG — derived dt from ISO:", dt)
            calendar_year = dt.year
            calendar_month = dt.month
            print("DEBUG — derived dt from ISO:", dt.year, dt.month)
        except ValueError:
            pass

        # Try "Apr-2024", "April 2024"
        if calendar_year is None:
            parts = v.replace("_", " ").replace("-", " ").split()
            for p in parts:
                p_lower = p.lower()
                if p_lower in MONTH_NAME_TO_INDEX:
                    calendar_month = MONTH_NAME_TO_INDEX[p_lower]
                elif p.isdigit() and len(p) == 4:
                    calendar_year = int(p)

    # -----------------------------
    # Validate extraction
    # -----------------------------
    if calendar_year is None or calendar_month is None:
        raise ValueError(
            f"Cannot derive fiscal year from value: {value}"
        )

    # -----------------------------
    # Fiscal year boundary logic
    # -----------------------------
    if calendar_month >= fiscal_year_start_month:
        return calendar_year
    else:
        return calendar_year - 1


def parse_fiscal_quarter(value):
    """
    Accepts:
    - Q1, Q2, Q3, Q4
    Returns:
    - 1–4
    """
    if value is None:
        return None

    if isinstance(value, str) and value.lower().startswith("q"):
        q = int(value[1])
        if 1 <= q <= 4:
            return q

    if isinstance(value, int) and 1 <= value <= 4:
        return value

    raise ValueError(f"Invalid fiscal quarter: {value}")


