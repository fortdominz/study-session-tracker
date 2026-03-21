# models.py
# Responsible for: validating and shaping data before it goes to db.py
# Nothing here touches the file system — that's db.py's job.

from datetime import datetime

# ── constants ─────────────────────────────────────────────────────────────────

SESSION_TYPES = ["Course", "Self-Study", "Research", "Practice"]

LOCATIONS = ["Library", "Home", "Café", "Classroom", "Other"]

# ── colors ────────────────────────────────────────────────────────────────────
# Used across ui.py for consistent styling. Import from here, never hardcode.

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
RED     = "\033[91m"

def c(text, color):
    """Wrap text in a color code and reset."""
    return f"{color}{text}{RESET}"

def bold(text):
    return f"{BOLD}{text}{RESET}"

def dim(text):
    return f"{DIM}{text}{RESET}"

# ── helpers ───────────────────────────────────────────────────────────────────

def validate_duration(raw):
    """
    Takes raw input string, returns (int_minutes, None) or (None, error_message).
    Must be a whole positive number.
    """
    try:
        value = int(raw.strip())
    except (ValueError, AttributeError):
        return None, "Please enter a whole number (e.g. 45)."
    if value <= 0:
        return None, "Duration must be greater than 0."
    return value, None


def validate_rating(raw):
    """
    Takes raw input string or empty string.
    Returns (int 1-5, None), (None, None) if skipped, or (None, error_message).
    """
    if not raw or raw.strip() == "":
        return None, None  # skipped — allowed
    try:
        value = int(raw.strip())
    except ValueError:
        return None, "Rating must be a number between 1 and 5."
    if value not in range(1, 6):
        return None, "Rating must be between 1 and 5."
    return value, None


def validate_mood(raw, label="Mood"):
    """
    Same as validate_rating — 1-5 or skip.
    label is used in error messages so caller can say 'Mood before' or 'Mood after'.
    """
    if not raw or raw.strip() == "":
        return None, None  # skipped — allowed
    try:
        value = int(raw.strip())
    except ValueError:
        return None, f"{label} must be a number between 1 and 5."
    if value not in range(1, 6):
        return None, f"{label} must be between 1 and 5."
    return value, None


def validate_date(raw):
    """
    Accepts YYYY-MM-DD format or empty (defaults to today).
    Returns (date_string, None) or (None, error_message).
    """
    if not raw or raw.strip() == "":
        return datetime.now().strftime("%Y-%m-%d"), None
    try:
        datetime.strptime(raw.strip(), "%Y-%m-%d")
        return raw.strip(), None
    except ValueError:
        return None, "Date must be in YYYY-MM-DD format (e.g. 2026-03-15)."


def format_duration(minutes):
    """Turns 90 into '1h 30m', 45 into '45m', 60 into '1h 0m'."""
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    remaining = minutes % 60
    if remaining == 0:
        return f"{hours}h"
    return f"{hours}h {remaining}m"


def format_date_display(date_str):
    """Turns '2026-03-15' into 'Mar 15, 2026'."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return date_str


def stars(rating):
    """Turns 4 into '★★★★☆'."""
    if rating is None:
        return "—"
    filled = "★" * rating
    empty = "☆" * (5 - rating)
    return filled + empty


def mood_label(value):
    """Turns 1-5 into a readable label."""
    if value is None:
        return "—"
    labels = {1: "Low", 2: "Below avg", 3: "Neutral", 4: "Good", 5: "Great"}
    return labels.get(value, "—")