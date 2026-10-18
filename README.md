# ai-companion-persona-kit

**A skeleton for a long-running AI companion character: persona-as-data, a daily situation engine, deterministic proactive messages, and a wellbeing guard.**

[![test](https://github.com/Kein-chronicle/ai-companion-persona-kit/actions/workflows/test.yml/badge.svg)](https://github.com/Kein-chronicle/ai-companion-persona-kit/actions/workflows/test.yml) ![license](https://img.shields.io/badge/license-MIT-blue.svg) ![dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)

## Why

The hard parts of a companion bot are not the prompt. They are what the character is doing right now, when it is allowed to speak first, and keeping attachment features from becoming dependence levers.

## Install

**From source:**

```sh
git clone https://github.com/Kein-chronicle/ai-companion-persona-kit.git
cd ai-companion-persona-kit
```

**Requires:** Python 3.10+.

## Quick start

Run the quickstart:

```console
$ python3 examples/quickstart.py
03:00  activity='offline for the night' availability=sleeping  proactive -> None  (quiet hours)
08:30  activity='cataloguing'  availability=busy      proactive -> None  (character is busy)
12:30  activity='listening break' availability=free      proactive -> share_something_found  (window match)

two unanswered messages -> (None, "previous proactive message unanswered: don't pile on")
```

The output above is real: it is produced by the files in `examples/`.

## Overview

Skeleton for a long-running **AI companion character** that lives in a chat app: a persona kept in files (not code),
a situation engine ("what is she doing right now?"), a deterministic proactive-message engine, a wellbeing guard, and a
chat/setting mode split, written around a **fictional** character
(`persona/juno.md`). No real person, likeness, voice, or conversation data is included - and the kit deliberately
omits image/voice-clone/intimacy modules.

| Module | What it does | Why it exists |
|---|---|---|
| `core/situation.py` | `current_activity(schedule, now)`; blocks wrap midnight | The character should have a life: answers in the middle of a "meeting" are slow, at 3 a.m. her simulated routine is offline |
| `core/routine.py` | day templates + repeat-avoiding picks with a **stable hash** | The original used `hash()` ("deterministic") which is salted per process - not reproducible |
| `core/proactive.py` | decides *whether* to speak and *which* scenario, no LLM call | Free, reproducible, testable. Restraints: opted-out or muted user, user said goodbye or is resting, quiet hours, character offline, unanswered message, daily cap, cooldown, user already chatting |
| `core/wellbeing.py` | `clean_exit / encourage_rest / normal / outward_nudge` + guidance text | Attachment levers are dependence levers; ship the safeguard with the feature. **Never guilt-trip a goodbye** |
| `core/modes.py` | chat mode cannot write `profile/`; change routing `generation/review/hybrid` | A chat message ("be more X") must not silently rewrite the persona |
| `persona/` | fictional SSOT + schedule + config examples | Personality lives in files, state in JSON |

```bash
python3 tests/run.py
```

### Safety and legal (read before connecting this to real users)

- **Openly an AI.** The persona never claims to be human, and its daily routine is a *simulated* fiction layer (`persona/juno.md`): it must say so if sincerely asked and must not claim bodily needs as fact.
- **Adults, and consent.** Intended for adult users. Proactive ("first") messages are unsolicited: honour an opt-out or mute (`state["opted_out"]`), pass the wellbeing mode in so a leaving or resting user is left alone, and make stopping them one tap.
- **Goodbyes.** The user can always leave. `wellbeing.mode(...)` returns `clean_exit` when the user said goodbye (`said_goodbye`) or is unavailable, and every guidance string repeats the no-guilt-trip rule. **The kit has no goodbye detector:** noticing "good night" is your application's job, and it must set `said_goodbye` (the proactive engine honours it too) and clear it when the user writes again. Do not disable the guard (`enabled: false` removes all of it).
- **Distress.** The kit has no crisis detection. If your users may be in distress, add one, and have the character drop the persona and point to real help (a trusted person, a local crisis line or emergency services).
- **Data.** Store as little as you can: timestamps and counters, not chat transcripts. Offer deletion on request, set a retention period, and follow the privacy law that applies to your users (for example GDPR or your national equivalent). The kit stores nothing by itself.
- **Not included on purpose:** image generation, voice cloning, any sexual content, any real person's likeness or voice.
- The profile guard (`core/modes.py`) protects against accidental edits by your own code; it is not a security boundary.

### Design rules

1. **Personality is data.** Keep identity in one SSOT file and keep the code thin; everything else references it.
2. **Classify every change request** before touching anything: `generation` (shape the first draft), `review` (judge results,
   suppress repeats, trigger regeneration) or `hybrid` (both; the default for tone, time-of-day fit, length, continuity).
   Prompts that only grow are a smell: put judgement in a review step. Promote repeated fixes into project rules, not session notes.
3. **Generate -> review -> patch/regenerate** loop beats one perfect prompt.
4. **Proactive messages are templates + gates**, not free generation; an LLM may polish wording downstream.
5. **No leftover manual overrides** in production: a forced mode or level that was added for a test and keeps winning over the real rules.
6. **Test isolation:** running a worker directly during tests can pollute live session state. Use a dump-only mode or an isolated state dir.
7. **Know your oldest interpreter:** `int | None` breaks on Python 3.9; use `Optional[int]` or require Python 3.10+.
8. When the persona's *concept* changes, grep every place that encoded the old concept (timers, state engines, docs, prompts).
9. Pin the priority order of any reference list explicitly. A workaround that quietly shortens it makes the character drift without any error.

## Limits

- The character, Juno, is fictional and openly an AI. The kit deliberately has no image generation, voice cloning or intimacy modules.

## Related projects

These solve neighbouring problems; use them when they fit better.

- **SillyTavern character cards**: define a persona prompt; this kit is the schedule, restraint and safeguard layer around one

## Development

```sh
python3 tests/run.py
```

The tests include inputs that are supposed to be rejected, so a green run also shows the checks can fail. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

If this saved you a debugging session, a star helps other people find it. Bug reports and failing test cases are even better.

<sub>Keywords: ai-companion, chatbot, persona, character, llm, python, telegram-bot, wellbeing</sub>
