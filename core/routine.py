"""Daily routine generation with repeat-avoidance. Deterministic and idempotent: the same (date, key) always picks the same item, even if you call it twice
with the same history (a worker restart must not change what the character "did today").
NOTE: Python's built-in hash() of a str is salted per process (PYTHONHASHSEED), so `hash(seed) % n` is NOT deterministic across runs. Use a stable hash."""
import hashlib, json

def stable_index(seed, n):
    return int(hashlib.sha256(seed.encode()).hexdigest(), 16) % n

def pick_without_repeat(pool, history, key, today, days_avoid=5):
    """history: {key: [{'date': 'YYYY-MM-DD', 'title': str}]} (mutated). Returns the chosen item (dict with 'title')."""
    if not pool: return {}
    from datetime import date, timedelta
    for r in history.get(key, []):                       # already chosen for today: return the same item, do not record a second one
        if r["date"] == today:
            same = [p for p in pool if p["title"] == r["title"]]
            if same: return same[0]
    cutoff = (date.fromisoformat(today) - timedelta(days=days_avoid)).isoformat()
    recent = {r["title"] for r in history.get(key, []) if r["date"] >= cutoff}
    candidates = [p for p in pool if p["title"] not in recent] or pool
    chosen = candidates[stable_index(f"{today}:{key}", len(candidates))]
    history.setdefault(key, []).append({"date": today, "title": chosen["title"]})
    history[key] = history[key][-20:]
    return chosen

def build_day(template, day_type, today, pools, history):
    """template: {'weekday': [{'start','activity','availability','pool'?}], 'weekend': [...], 'holiday': [...]}.
    A block with 'pool' gets its activity detail picked from pools[pool] without recent repeats."""
    out = []
    for b in template[day_type]:
        b = dict(b)
        if "pool" in b:
            pick = pick_without_repeat(pools[b["pool"]], history, b["pool"], today)
            b["detail"] = pick.get("title", "")
        out.append(b)
    return out
