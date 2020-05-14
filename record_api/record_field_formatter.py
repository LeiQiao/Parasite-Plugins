from datetime import datetime

def datetime_formatter(dt):
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return dt


def date_formatter(dt):
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d')
    else:
        return dt


def value_10_formatter(v):
    if v is not None or (isinstance(v, bool) and v):
        return 1
    else:
        return 0

def none_to_0_formatter(v):
    if v is None:
        return 0
    else:
        return v