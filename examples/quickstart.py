"""What is the character doing right now, and should she message you? Everything is deterministic and needs no LLM."""
import json, os, sys
from datetime import datetime
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(root, "core"))
import situation, proactive, wellbeing

sched = json.load(open(os.path.join(root, "persona", "schedule.example.json")))
cfg = json.load(open(os.path.join(root, "persona", "config.example.json")))

for hhmm in ("03:00", "08:30", "12:30"):
    when = datetime(2026, 3, 4, *map(int, hhmm.split(":")))
    act = situation.current_activity(sched["weekday"], when)
    state = {"day_type": "weekday", "unanswered": 0, "sent_today": 0}
    scenario, why = proactive.decide(when, act, state, cfg["proactive"])
    print(f"{hhmm}  activity={act['activity']!r:14} availability={act['availability']:9} proactive -> {scenario}  ({why})")

print()
state = {"day_type": "weekday", "unanswered": 2, "sent_today": 0}
when = datetime(2026, 3, 4, 8, 30)
print("two unanswered messages ->", proactive.decide(when, {"availability": "free"}, state, cfg["proactive"]))
