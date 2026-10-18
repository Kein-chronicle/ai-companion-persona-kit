"""Proactive ("first-message") engine. DETERMINISTIC TEMPLATES, not an LLM call: free to run, reproducible, testable.
Decides whether to speak and which scenario; wording comes from templates (an LLM may polish them downstream)."""
from datetime import datetime, timedelta

def in_quiet_hours(now, quiet):            # quiet = ('00:30', '07:05'), may wrap midnight
    s, e = (tuple(map(int, x.split(":"))) for x in quiet); t = (now.hour, now.minute)
    return (s <= t < e) if s < e else (t >= s or t < e)

def _in_window(t, a, b):          # a window may wrap midnight: ("22:00", "01:00")
    return (a <= t < b) if a < b else (t >= a or t < b)

def _iso(v, now):
    d = datetime.fromisoformat(v)
    if (d.tzinfo is None) != (now.tzinfo is None): raise ValueError("state timestamps and `now` must both be naive local times or both timezone-aware")
    return d

def _count(state, key):
    v = state.get(key, 0)
    if v is None: return 0
    if isinstance(v, bool) or not isinstance(v, int) or v < 0: raise ValueError(f"state['{key}'] must be a non-negative integer, got {v!r}")
    return v

def decide(now, activity, state, cfg):
    """state: {'last_proactive': iso|None, 'last_user_msg': iso|None, 'sent_today': int, 'unanswered': int, 'opted_out': bool, 'said_goodbye': bool, 'wellbeing_mode': str|None}
    returns (scenario_id | None, reason). Unsolicited messages need consent: an opted-out or muted user never gets one, and neither does a user
    who is leaving or being sent to rest (pass the mode from wellbeing.mode as state['wellbeing_mode'])."""
    if state.get("opted_out") or state.get("muted"): return None, "user opted out or muted proactive messages"
    if state.get("said_goodbye"): return None, "user said goodbye: the caller clears this flag when the user writes again or at its own expiry"
    wm = str(state.get("wellbeing_mode") or "").strip().lower()
    if wm in ("clean_exit", "encourage_rest"): return None, f"user is leaving or resting ({wm}): no unsolicited messages"
    if in_quiet_hours(now, cfg["quiet_hours"]): return None, "quiet hours"
    av = str((activity or {}).get("availability") or "").strip().lower()
    if av in ("sleeping", "busy", "offline", "away", "unavailable"): return None, f"character is {av}"
    if _count(state, "unanswered") >= cfg.get("max_unanswered", 1): return None, "previous proactive message unanswered: don't pile on"
    if _count(state, "sent_today") >= cfg.get("max_per_day", 3): return None, "daily cap reached"
    lp = state.get("last_proactive")
    if lp and now - _iso(lp, now) < timedelta(minutes=cfg.get("cooldown_min", 90)): return None, "cooldown"
    lu = state.get("last_user_msg")
    if lu and now - _iso(lu, now) < timedelta(minutes=cfg.get("recent_chat_min", 30)): return None, "user is already chatting"
    for sc in cfg["scenarios"]:                       # first scenario whose window matches wins (ordered by priority)
        a, b = (tuple(map(int, x.split(":"))) for x in sc["window"]); t = (now.hour, now.minute)
        if _in_window(t, a, b) and (not sc.get("day_types") or state.get("day_type") in sc["day_types"]): return sc["id"], "window match"
    return None, "no scenario window"
