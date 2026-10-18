import json, os, sys
from datetime import datetime, date
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.join(here, ".."); sys.path.insert(0, os.path.join(root, "core"))
import situation, routine, proactive, wellbeing, modes
ok = True
def expect(n, got, want):
    global ok; g = got == want; ok &= g; print(("ok   " if g else "FAIL ") + f"{n}: {got!r}" + ("" if g else f" (want {want!r})"))
sched = json.load(open(os.path.join(root, "persona", "schedule.example.json"))); cfg = json.load(open(os.path.join(root, "persona", "config.example.json")))

# situation engine
wd = sched["weekday"]
expect("noon -> listening break", situation.current_activity(wd, datetime(2026, 3, 4, 12, 30))["activity"], "listening break")
expect("03:00 wraps to previous day's last block (offline for the night)", situation.current_activity(wd, datetime(2026, 3, 4, 3, 0))["activity"], "offline for the night")
expect("day type: Saturday", situation.day_type(date(2026, 3, 7)), "weekend")
expect("day type: holiday wins", situation.day_type(date(2026, 3, 4), holidays={"2026-03-04"}), "holiday")

# routine: stable and repeat-avoiding
pool = sched["pools"]["playlists"]; hist = {}
picks = [routine.pick_without_repeat(pool, hist, "playlists", f"2026-03-{d:02d}")["title"] for d in range(1, 6)]
expect("5 consecutive days never repeat inside the 5-day window", len(set(picks)), 5)
h1, h2 = {}, {}
expect("same date => same pick (stable hash, not salted hash())", routine.pick_without_repeat(pool, h1, "playlists", "2026-03-09"), routine.pick_without_repeat(pool, h2, "playlists", "2026-03-09"))
expect("empty pool => {}", routine.pick_without_repeat([], {}, "x", "2026-03-01"), {})

# proactive: every restraint
P = cfg["proactive"]; wk = {"day_type": "weekday", "unanswered": 0, "sent_today": 0}
free = {"availability": "free"}
expect("good window, free, quiet state => morning greeting", proactive.decide(datetime(2026, 3, 4, 8, 30), free, wk, P)[0], "morning_greeting")
expect("quiet hours => silent", proactive.decide(datetime(2026, 3, 4, 3, 0), free, wk, P)[0], None)
expect("character offline (sleeping availability) => silent", proactive.decide(datetime(2026, 3, 4, 8, 30), {"availability": "sleeping"}, wk, P)[0], None)
expect("unanswered previous message => do not pile on", proactive.decide(datetime(2026, 3, 4, 8, 30), free, dict(wk, unanswered=1), P)[0], None)
expect("daily cap", proactive.decide(datetime(2026, 3, 4, 8, 30), free, dict(wk, sent_today=3), P)[0], None)
expect("cooldown", proactive.decide(datetime(2026, 3, 4, 8, 30), free, dict(wk, last_proactive="2026-03-04T07:30:00"), P)[0], None)
expect("user already chatting", proactive.decide(datetime(2026, 3, 4, 8, 30), free, dict(wk, last_user_msg="2026-03-04T08:20:00"), P)[0], None)
expect("no window match", proactive.decide(datetime(2026, 3, 4, 16, 0), free, wk, P)[0], None)

# wellbeing
W = cfg["wellbeing"]
expect("user leaving => clean exit (beats everything)", wellbeing.mode(datetime(2026, 3, 4, 2, 0), {"availability": "sleeping", "chatting": True}, W)[0], "clean_exit")
expect("late and still chatting => encourage rest", wellbeing.mode(datetime(2026, 3, 4, 2, 0), {"chatting": True}, W)[0], "encourage_rest")
modes_seen = {wellbeing.mode(datetime(2026, 3, d, 15, 0), {"chatting": False}, W)[0] for d in range(1, 29)}
expect("daytime: only normal or outward_nudge, and the nudge is occasional", modes_seen, {"normal", "outward_nudge"})
expect("every guidance string carries the no-guilt-goodbye rule", all("never guilt-trip or hold back a goodbye" in g.lower() for g in wellbeing.GUIDANCE.values()), True)

# modes
try: modes.assert_can_write("chat", "/x/persona/profile/identity.md"); expect("chat mode may not edit the profile", "no error", "ModeViolation")
except modes.ModeViolation: expect("chat mode may not edit the profile", True, True)
modes.assert_can_write("setting", "/x/persona/profile/identity.md"); expect("setting mode may", True, True)
modes.assert_can_write("chat", "/x/state/log.json"); expect("chat mode may write state", True, True)
expect("unclassifiable change defaults to hybrid", modes.classify_change("make her feel more natural"), "hybrid")

# --- review findings
h = {}; pool = sched["pools"]["playlists"]
first = routine.pick_without_repeat(pool, h, "pl", "2026-03-09"); again = routine.pick_without_repeat(pool, h, "pl", "2026-03-09")
expect("same history, same day => the same pick (idempotent across a restart)", (first, len(h["pl"])), (again, 1))
expect("a goodbye is always a clean exit, even at 15:00 while chatting", wellbeing.mode(datetime(2026, 3, 4, 15, 0), {"said_goodbye": True, "chatting": True}, W)[0], "clean_exit")
nudge_day = next(datetime(2026, 3, d, 15, 0) for d in range(1, 29) if wellbeing.mode(datetime(2026, 3, d, 15, 0), {}, W)[0] == "outward_nudge")
expect("an outward nudge happens once a day (nudged_today suppresses it)", wellbeing.mode(nudge_day, {"nudged_today": True}, W)[0], "normal")
expect("the guard disabled is still the plain mode with the goodbye rule in its guidance", "goodbye" in wellbeing.mode(nudge_day, {}, dict(W, enabled=False))[1].lower(), True)
expect("opted-out user never gets a proactive message", proactive.decide(datetime(2026, 3, 4, 8, 30), free, dict(wk, opted_out=True), P)[0], None)
expect("muted user never gets a proactive message", proactive.decide(datetime(2026, 3, 4, 8, 30), free, dict(wk, muted=True), P)[0], None)
expect("a leaving user (wellbeing clean_exit) is left alone", proactive.decide(datetime(2026, 3, 4, 8, 30), free, dict(wk, wellbeing_mode="clean_exit"), P)[0], None)
wrap = dict(P, scenarios=[{"id": "late_check_in", "window": ["22:00", "23:50"]}, {"id": "night_owl", "window": ["22:00", "01:00"]}], quiet_hours=["03:00", "04:00"])
expect("a scenario window that wraps midnight matches after midnight", proactive.decide(datetime(2026, 3, 4, 0, 30), free, wk, dict(wrap, scenarios=[wrap["scenarios"][1]]))[0], "night_owl")
for label, bad in (("unanswered=None counts as 0", dict(wk, unanswered=None)),):
    expect(label, proactive.decide(datetime(2026, 3, 4, 8, 30), free, bad, P)[0], "morning_greeting")
try: proactive.decide(datetime(2026, 3, 4, 8, 30), free, dict(wk, sent_today="3"), P); expect("a string counter is rejected clearly", "no error", "ValueError")
except ValueError: expect("a string counter is rejected clearly", True, True)
try: proactive.decide(datetime(2026, 3, 4, 8, 30), free, dict(wk, last_user_msg="2026-03-04T08:00:00+09:00"), P); expect("mixing aware and naive timestamps is rejected clearly", "no error", "ValueError")
except ValueError: expect("mixing aware and naive timestamps is rejected clearly", True, True)
try: situation.parse_hhmm("7am"); expect("a bad time string is rejected with a clear message", "no error", "ValueError")
except ValueError as e: expect("a bad time string is rejected with a clear message", "HH:MM" in str(e), True)
for path in ("/x/Profile/id.md", "/x/PERSONA/PROFILE/id.md", "x\\profile\\a"):
    try: modes.assert_can_write("chat", path); expect(f"profile guard is case/separator-insensitive: {path}", "no error", "ModeViolation")
    except modes.ModeViolation: expect(f"profile guard is case/separator-insensitive: {path}", True, True)
expect("proactive engine itself honours said_goodbye even after the chat cooldown", proactive.decide(datetime(2026, 3, 4, 20, 15), free, dict(wk, last_user_msg="2026-03-04T19:40:00", said_goodbye=True), P)[0], None)
expect("wellbeing_mode is compared case-insensitively", proactive.decide(datetime(2026, 3, 4, 8, 30), free, dict(wk, wellbeing_mode="Clean_Exit"), P)[0], None)
for av in ("Sleeping", "offline", "In a meeting"):
    expect(f"availability {av!r} is a departure for the wellbeing guard", wellbeing.mode(datetime(2026, 3, 4, 15, 0), {"availability": av}, W)[0], "clean_exit")
expect("an 'Offline' character is silent", proactive.decide(datetime(2026, 3, 4, 8, 30), {"availability": "Offline"}, wk, P)[0], None)
sys.exit(0 if ok else 1)

