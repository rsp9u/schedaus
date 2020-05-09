import re
import base64
from string import hexdigits
from datetime import datetime, date, timedelta

from schedaus.svg_colors import svg_colors


def decode_base64url(s):
    return base64.urlsafe_b64decode(s + '=' * ((4 - len(s) & 3) & 3)).decode()


def get_prefix_space_num(s):
    for match in re.finditer("[^\\s]", s):
        return match.start()
    return 0


def strpdate(s, fmt="%Y/%m/%d"):
    if s is None:
        return None
    dt = datetime.strptime(s, fmt)
    return date(dt.year, dt.month, dt.day)


def weekday_to_dates(weekday, start, end):
    dates = []
    weekday = weekday.lower()[0:2]
    d = date(start.year, start.month, start.day)
    while d != (end + timedelta(days=1)):
        if d.strftime("%a").lower()[0:2] == weekday:
            dates.append(d)
        d = date(d.year, d.month, d.day)
        d += timedelta(days=1)
    return dates


def calc_date_in_business_days(start, days, holidays):
    if days == 0 or days == 1 or days == -1:
        return date(start.year, start.month, start.day)

    delta = 1 if days > 0 else -1
    ret = date(start.year, start.month, start.day)

    i = days
    while True:
        if ret not in holidays:
            i -= delta
        if i == 0:
            break
        ret += timedelta(days=delta)

    return ret


def calc_business_days(start, end, holidays):
    days = 0
    d = date(start.year, start.month, start.day)
    while d != (end + timedelta(days=1)):
        if d not in holidays:
            days += 1
        d += timedelta(days=1)
    return days


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_valid_date(s):
    try:
        strpdate(s)
        return True
    except ValueError:
        return False


def is_valid_color(color):
    if color.startswith("#") and len(color) == 7 and all([char in hexdigits for char in color[1:]]):
        return True
    if color in svg_colors:
        return True
    return False
