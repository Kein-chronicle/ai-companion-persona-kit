"""Two-mode separation: CHAT mode talks as the character; SETTING mode edits the character. Only SETTING may write profile files.
This stops a chat message ('be more X') from silently rewriting the persona. It is a guard against ACCIDENTAL edits by your own code, not a security boundary:
real protection needs file permissions."""
import os
PROFILE_DIR_NAME = "profile"

class ModeViolation(Exception): pass

def assert_can_write(mode, path):
    parts = os.path.realpath(path).replace("\\", "/").lower().split("/")           # symlinks resolved, case-insensitive, either separator
    if PROFILE_DIR_NAME in parts and mode != "setting":
        raise ModeViolation(f"{mode} mode cannot modify {path}; switch to setting mode")

def classify_change(request_text, kinds=None):
    """generation / review / hybrid routing. Default 'hybrid': most requirements must shape the first draft AND be re-checked after.
    generation: choose direction/prompt/selection. review: judge results, repeat suppression, regeneration triggers."""
    t = request_text.lower()
    review = any(k in t for k in ("reject", "fail if", "detect repeat", "check that", "must not appear", "verify"))
    gen = any(k in t for k in ("tone", "style", "prefer", "start with", "choose", "pattern for"))
    if review and not gen: return "review"
    if gen and not review: return "generation"
    return "hybrid"
