from persiantools.jdatetime import JalaliDate

from datetime import datetime


def convert_to_jalali(gregorian_date):

    try:
        if isinstance(gregorian_date, str):
            gregorian_date = datetime.strptime(gregorian_date, "%Y-%m-%d").date()
        jalali_date = JalaliDate(gregorian_date)
        return int(jalali_date.strftime("%Y%m%d"))
    except Exception as e:
        print(f"Error converting date {gregorian_date}: {e}")
        return None



time_now = datetime.now().strftime("%Y-%m-%d")
converted_time = convert_to_jalali(time_now)
print(converted_time)