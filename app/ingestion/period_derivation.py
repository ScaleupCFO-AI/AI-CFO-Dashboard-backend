from datetime import date, datetime
import calendar

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


def extract_calendar_month(value) -> int:
    if value is None:
        raise ValueError("Cannot extract month from None")

    if isinstance(value, (date, datetime)):
        return value.month

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).month
        except ValueError:
            pass

        key = value.lower().split()[0]
        if key in MONTH_NAME_TO_INDEX:
            return MONTH_NAME_TO_INDEX[key]

    raise ValueError(f"Unsupported month value: {value}")



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

    Returns:
    - fiscal_year (int)
    """

    if value is None:
        raise ValueError("period_date cannot be None")

    # -----------------------------
    # Normalize to datetime.date
    # -----------------------------
    if isinstance(value, datetime):
        dt = value

    elif isinstance(value, date):
        dt = datetime.combine(value, datetime.min.time())

    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            raise ValueError(f"Invalid ISO date string: {value}")

    else:
        raise ValueError(f"Unsupported date type: {type(value)}")

    calendar_year = dt.year
    calendar_month = dt.month

    # -----------------------------
    # Fiscal year boundary logic
    # -----------------------------
    if calendar_month >= fiscal_year_start_month:
        return calendar_year
    else:
        return calendar_year - 1



def derive_period_dates(
    period_type: str,
    fiscal_year: int,
    fiscal_quarter: int | None,
    fiscal_month: int | None,
    fiscal_year_start_month: int,
):
    if period_type == "month":
        if fiscal_month is None:
            raise ValueError("Monthly period requires fiscal_month")

        year_offset = 1 if fiscal_month < fiscal_year_start_month else 0
        year = fiscal_year - year_offset

        start = date(year, fiscal_month, 1)
        end = date(year, fiscal_month, calendar.monthrange(year, fiscal_month)[1])
        return start, end

    if period_type == "quarter":
        if fiscal_quarter is None:
            raise ValueError("Quarterly period requires fiscal_quarter")

        start_month = ((fiscal_year_start_month - 1) + (fiscal_quarter - 1) * 3) % 12 + 1
        year = fiscal_year if start_month >= fiscal_year_start_month else fiscal_year + 1

        start = date(year, start_month, 1)
        end_month = (start_month + 2 - 1) % 12 + 1
        end_year = year if end_month >= start_month else year + 1

        end = date(end_year, end_month, calendar.monthrange(end_year, end_month)[1])
        return start, end

    if period_type == "year":
        start = date(fiscal_year, fiscal_year_start_month, 1)
        end_month = fiscal_year_start_month - 1 or 12
        end_year = fiscal_year if fiscal_year_start_month > 1 else fiscal_year + 1
        end = date(end_year, end_month, calendar.monthrange(end_year, end_month)[1])
        return start, end

    raise ValueError(f"Unsupported period_type: {period_type}")
