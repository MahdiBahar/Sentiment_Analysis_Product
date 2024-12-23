# Import libraries
from persiantools.jdatetime import JalaliDate
from datetime import datetime

def convert_to_jalali(gregorian_date):
    """Convert a Gregorian date to Jalali date in YYYYMMDD integer format."""
    try:
        if isinstance(gregorian_date, str):
            gregorian_date = datetime.strptime(gregorian_date, "%Y-%m-%d").date()
        jalali_date = JalaliDate(gregorian_date)
        return int(jalali_date.strftime("%Y%m%d"))
    except Exception as e:
        print(f"Error converting date {gregorian_date}: {e}")
        return None

