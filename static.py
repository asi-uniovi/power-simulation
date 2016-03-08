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

# And these to bytes.
KB = lambda x: x << 10
MB = lambda x: x << 20


def weight(x, ip, fp):
    """Linear increment between ip and fp function."""
    return max(0, min(1, (ip - x) / (ip - fp)))


def weighted_user_satisfaction(t, timeout):
    """Calculates the weighted satisfaction with a sigmoid."""
    if t <= timeout:
        return 1
    else:
        return weight(t - timeout, 1, 300)
