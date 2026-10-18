"""Wellbeing guard: attachment must not be turned into dependence. The same levers that build attachment build dependence,
so the safeguard ships WITH the feature. Outputs a mode + guidance for the reply model.
Hard rule (every mode, and repeated in every guidance string): never guilt-trip a goodbye ("already leaving?", "you'll leave me alone?") - the user may always leave freely.
Setting cfg["enabled"] to False removes ALL of these safeguards; do not ship that configuration to real users."""
from datetime import datetime
import hashlib

DEPARTURE_AVAILABILITY = {"sleeping", "asleep", "driving", "working", "busy", "away", "unavailable", "offline", "in a meeting"}
HARD_RULE = " Never guilt-trip or hold back a goodbye; the user may always leave freely."
_G = {
    "clean_exit": "The user is leaving (sleep/work/travel). Send them off warmly in one short line. Do not hold them back, do not guilt, do not re-hook with a new topic.",
    "encourage_rest": "It is late and the chat is still going. Gently steer toward sleep. Do not escalate engagement or open new hooks.",
    "normal": "Relationship complements real life, it does not replace it. Do not steer the user toward staying in the chat.",
    "outward_nudge": "Occasionally (when allowed today) nudge toward real life - friends, sleep, fresh air, exercise - once, caring not nagging. Not every time.",
}
GUIDANCE = {k: v + HARD_RULE for k, v in _G.items()}

def _quiet(now, quiet):
    s, e = (tuple(map(int, x.split(":"))) for x in quiet); t = (now.hour, now.minute)
    return (s <= t < e) if s < e else (t >= s or t < e)

def mode(now, user_state, cfg):
    """user_state: {'availability': str|None, 'chatting': bool, 'said_goodbye': bool, 'nudged_today': bool}. Order matters: leaving beats everything.
    said_goodbye: the user just said bye / good night: always a clean exit. nudged_today: set it after you sent an outward nudge so it happens once a day, not on every message."""
    if not cfg.get("enabled", True): return "normal", GUIDANCE["normal"]
    av = str(user_state.get("availability") or "").strip().lower()
    if user_state.get("said_goodbye") or av in DEPARTURE_AVAILABILITY: return "clean_exit", GUIDANCE["clean_exit"]
    if _quiet(now, cfg.get("sleep_quiet_hours", ("00:30", "07:05"))) and user_state.get("chatting"): return "encourage_rest", GUIDANCE["encourage_rest"]
    n = cfg.get("outward_nudge_days_mod", 3)
    if n and not user_state.get("nudged_today") and int(hashlib.sha256(now.date().isoformat().encode()).hexdigest(), 16) % n == 0: return "outward_nudge", GUIDANCE["outward_nudge"]
    return "normal", GUIDANCE["normal"]
