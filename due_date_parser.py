import re
from datetime import datetime
from dateutil import parser as dateutil_parser

SCHEDULED_MARKER = "[SCHEDULED]"
DUE_PATTERN = re.compile(r'\[DUE ([^\]]+)\]', re.IGNORECASE)
TIME_PATTERN = re.compile(r'\b\d{1,2}:\d{2}|\b\d{1,2}\s*(?:am|pm)\b', re.IGNORECASE)


def extract_due(line):
    """
    Parse [DUE ...] from a todo line.
    Returns (due_str, datetime_obj, is_whole_day) or None if no [DUE ...] found or unparseable.
    is_whole_day=True if only a date was given (no time component).
    """
    match = DUE_PATTERN.search(line)
    if not match:
        return None

    due_str = match.group(1).strip()
    now = datetime.now()
    default_dt = datetime(now.year, now.month, now.day)

    try:
        parsed = dateutil_parser.parse(due_str, default=default_dt)
    except (ValueError, OverflowError):
        return None

    is_whole_day = not bool(TIME_PATTERN.search(due_str))
    return due_str, parsed, is_whole_day


def is_scheduled(line):
    return SCHEDULED_MARKER in line


def mark_scheduled(line):
    return line.rstrip('\n') + f' {SCHEDULED_MARKER}\n'
