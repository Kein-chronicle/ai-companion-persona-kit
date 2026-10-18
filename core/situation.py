"""Situation engine: what is the character doing RIGHT NOW? Pure function of (schedule, time) - no LLM call."""
from datetime import datetime, time, timedelta

def parse_hhmm(s):
    try: h, m = str(s).split(":"); return time(int(h), int(m))
    except ValueError: raise ValueError(f"bad time {s!r}: use HH:MM between 00:00 and 23:59")

def current_activity(schedule, now):
    """schedule: ordered list of {'start': 'HH:MM', 'activity': str, 'availability': 'free|busy|away|sleeping', ...}.
    Blocks may cross midnight (the last block runs until the first block of the next day)."""
    if not schedule: return None
    blocks = sorted(schedule, key=lambda b: parse_hhmm(b["start"]))
    t = now.time(); cur = blocks[-1]                      # before the first block => still in yesterday's last block
    for b in blocks:
        if parse_hhmm(b["start"]) <= t: cur = b
    return cur

def day_type(date, holidays=()):
    iso = date.isoformat()
    if iso in holidays: return "holiday"
    return "weekend" if date.weekday() >= 5 else "weekday"
