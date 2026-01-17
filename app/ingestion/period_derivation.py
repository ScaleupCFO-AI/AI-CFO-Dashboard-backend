from datetime import date
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


