"""Static definitions, such as constants."""

DAYS = {
    'Sunday': 0,
    'Monday': 1,
    'Tuesday': 2,
    'Wednesday': 3,
    'Thursday': 4,
    'Friday': 5,
    'Saturday': 6,
}

INV_DAYS = {v: k for k, v in DAYS.items()}

# All this functions convert to seconds.
HOUR = lambda x: x * 3600.0
DAY = lambda x: x * HOUR(24)
WEEK = lambda x: x * DAY(7)