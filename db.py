import json
import os
import uuid
from datetime import datetime

# ── paths ────────────────────────────────────────────────────────────────────
DB_FILE = "study_tracker.json"

# ── default structure ────────────────────────────────────────────────────────
def _default_db():
    return {
        "meta": {
            "created_date": datetime.now().isoformat(),
            "version": "1.0"
        },
        "subjects": [],
        "sessions": [],
        "deleted_sessions": [],   # permanent log — never cleared
        "archived_topics": []     # permanent log — never cleared
    }


def _migrate(db):
    """
    Adds missing keys to existing JSON files so old data
    is not lost when new fields are introduced.
    """
    if "deleted_sessions" not in db:
        db["deleted_sessions"] = []
    if "archived_topics" not in db:
        db["archived_topics"] = []
    return db

# ── load / save ───────────────────────────────────────────────────────────────
def load_db():
    if not os.path.exists(DB_FILE):
        db = _default_db()
        save_db(db)
        return db
    with open(DB_FILE, "r") as f:
        db = json.load(f)
    return _migrate(db)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ── subject CRUD ──────────────────────────────────────────────────────────────
def create_subject(name, default_type):
    """Returns (subject, None) on success or (None, error_message) on failure."""
    db = load_db()

    name = name.strip()
    if not name:
        return None, "Subject name cannot be empty."

    # duplicate check (case-insensitive, active subjects only)
    for s in db["subjects"]:
        if s["name"].lower() == name.lower() and not s["archived"]:
            return None, f"Subject '{name}' already exists."

    subject = {
        "id": str(uuid.uuid4()),
        "name": name,
        "default_type": default_type,
        "created_date": datetime.now().isoformat(),
        "archived": False
    }

    db["subjects"].append(subject)
    save_db(db)
    return subject, None


def get_all_subjects(include_archived=False):
    db = load_db()
    if include_archived:
        return db["subjects"]
    return [s for s in db["subjects"] if not s["archived"]]


def get_subject_by_id(subject_id):
    db = load_db()
    for s in db["subjects"]:
        if s["id"] == subject_id:
            return s
    return None


def update_subject(subject_id, fields):
    """
    fields: dict of keys to update — name, default_type, archived.
    Returns (updated_subject, None) or (None, error_message).
    """
    db = load_db()
    for i, s in enumerate(db["subjects"]):
        if s["id"] == subject_id:
            # name uniqueness check if renaming
            if "name" in fields:
                new_name = fields["name"].strip()
                if not new_name:
                    return None, "Subject name cannot be empty."
                for other in db["subjects"]:
                    if (other["id"] != subject_id
                            and other["name"].lower() == new_name.lower()
                            and not other["archived"]):
                        return None, f"Subject '{new_name}' already exists."
                fields["name"] = new_name

            db["subjects"][i].update(fields)
            save_db(db)
            return db["subjects"][i], None

    return None, "Subject not found."


def archive_subject(subject_id):
    """
    Archives a topic and writes a permanent snapshot to archived_topics log.
    Returns (updated_subject, None) or (None, error_message).
    """
    db = load_db()

    subject = get_subject_by_id(subject_id)
    if not subject:
        return None, "Subject not found."

    # calculate totals at time of archiving
    total_sessions = len([s for s in db["sessions"] if s["subject_id"] == subject_id])
    total_minutes = sum(s["duration_minutes"] for s in db["sessions"] if s["subject_id"] == subject_id)

    # write permanent snapshot
    snapshot = {
        "id": subject["id"],
        "name": subject["name"],
        "default_type": subject["default_type"],
        "created_date": subject["created_date"],
        "archived_at": datetime.now().isoformat(),
        "total_sessions": total_sessions,
        "total_minutes": total_minutes
    }
    db["archived_topics"].append(snapshot)
    save_db(db)

    return update_subject(subject_id, {"archived": True})


# ── session CRUD ──────────────────────────────────────────────────────────────
def create_session(subject_id, session_type, duration_minutes,
                   date, location, rating, mood_before, mood_after, notes):
    """Returns (session, None) on success or (None, error_message) on failure."""
    db = load_db()

    # validate subject exists and is active
    subject = get_subject_by_id(subject_id)
    if not subject:
        return None, "Subject not found."
    if subject["archived"]:
        return None, "Cannot log a session for an archived subject."

    # validate duration
    if not isinstance(duration_minutes, int) or duration_minutes <= 0:
        return None, "Duration must be a positive whole number of minutes."

    # validate rating
    if rating is not None and rating not in range(1, 6):
        return None, "Rating must be between 1 and 5."

    # validate mood fields
    for label, val in [("mood_before", mood_before), ("mood_after", mood_after)]:
        if val is not None and val not in range(1, 6):
            return None, f"{label} must be between 1 and 5."

    session = {
        "id": str(uuid.uuid4()),
        "subject_id": subject_id,
        "session_type": session_type,
        "duration_minutes": duration_minutes,
        "date": date,                   # stored as "YYYY-MM-DD" string
        "location": location,           # string or None
        "rating": rating,               # int 1-5 or None
        "mood_before": mood_before,     # int 1-5 or None
        "mood_after": mood_after,       # int 1-5 or None
        "notes": notes,                 # string or None
        "created_at": datetime.now().isoformat()
    }

    db["sessions"].append(session)
    save_db(db)
    return session, None


def get_all_sessions():
    db = load_db()
    return db["sessions"]


def get_sessions_by_subject(subject_id):
    db = load_db()
    return [s for s in db["sessions"] if s["subject_id"] == subject_id]


def get_sessions_by_date(date_str):
    """date_str: 'YYYY-MM-DD'"""
    db = load_db()
    return [s for s in db["sessions"] if s["date"] == date_str]


def get_session_by_id(session_id):
    db = load_db()
    for s in db["sessions"]:
        if s["id"] == session_id:
            return s
    return None


def update_session(session_id, fields):
    """
    fields: dict of keys to update.
    Returns (updated_session, None) or (None, error_message).
    """
    db = load_db()
    for i, s in enumerate(db["sessions"]):
        if s["id"] == session_id:
            # validate duration if updating
            if "duration_minutes" in fields:
                d = fields["duration_minutes"]
                if not isinstance(d, int) or d <= 0:
                    return None, "Duration must be a positive whole number of minutes."
            # validate rating if updating
            if "rating" in fields:
                r = fields["rating"]
                if r is not None and r not in range(1, 6):
                    return None, "Rating must be between 1 and 5."
            # validate mood fields if updating
            for mood_key in ["mood_before", "mood_after"]:
                if mood_key in fields:
                    val = fields[mood_key]
                    if val is not None and val not in range(1, 6):
                        return None, f"{mood_key} must be between 1 and 5."

            db["sessions"][i].update(fields)
            save_db(db)
            return db["sessions"][i], None

    return None, "Session not found."


def delete_session(session_id):
    """
    Deletes a session and writes a permanent snapshot to deleted_sessions log.
    Returns (True, None) on success or (None, error_message) on failure.
    """
    db = load_db()
    for i, s in enumerate(db["sessions"]):
        if s["id"] == session_id:
            # capture topic name at time of deletion
            subject = get_subject_by_id(s["subject_id"])
            topic_name = subject["name"] if subject else "Unknown (topic deleted)"

            # write permanent snapshot
            snapshot = {
                **s,                                        # all session fields
                "topic_name": topic_name,                  # readable name preserved
                "deleted_at": datetime.now().isoformat()   # when it was deleted
            }
            db["deleted_sessions"].append(snapshot)
            db["sessions"].pop(i)
            save_db(db)
            return True, None
    return None, "Session not found."


# ── analytics helpers (raw data only — no display logic) ─────────────────────
def get_total_minutes_by_subject():
    """Returns {subject_id: total_minutes}."""
    db = load_db()
    totals = {}
    for s in db["sessions"]:
        sid = s["subject_id"]
        totals[sid] = totals.get(sid, 0) + s["duration_minutes"]
    return totals


def get_sessions_in_date_range(start_date, end_date):
    """
    start_date, end_date: 'YYYY-MM-DD' strings (inclusive).
    """
    db = load_db()
    return [
        s for s in db["sessions"]
        if start_date <= s["date"] <= end_date
    ]


def get_deleted_sessions():
    """Returns the permanent deleted sessions log, newest first."""
    db = load_db()
    return sorted(db["deleted_sessions"], key=lambda s: s["deleted_at"], reverse=True)


def get_archived_topics():
    """Returns the permanent archived topics log, newest first."""
    db = load_db()
    return sorted(db["archived_topics"], key=lambda t: t["archived_at"], reverse=True)


def unarchive_subject(subject_id):
    """
    Restores an archived topic back to active.
    Returns (updated_subject, None) or (None, error_message).
    """
    return update_subject(subject_id, {"archived": False})


def get_streak():
    """
    Returns the current daily study streak (consecutive days ending today
    or yesterday that have at least one session).
    """
    from datetime import date, timedelta

    db = load_db()
    if not db["sessions"]:
        return 0

    study_dates = set(s["date"] for s in db["sessions"])

    streak = 0
    check = date.today()

    if check.isoformat() not in study_dates:
        check -= timedelta(days=1)

    while check.isoformat() in study_dates:
        streak += 1
        check -= timedelta(days=1)

    return streak


def get_longest_streak():
    """
    Returns the longest streak of consecutive study days ever recorded.
    """
    from datetime import date, timedelta

    db = load_db()
    if not db["sessions"]:
        return 0

    study_dates = sorted(set(s["date"] for s in db["sessions"]))
    if not study_dates:
        return 0

    longest = 1
    current = 1

    for i in range(1, len(study_dates)):
        prev = datetime.strptime(study_dates[i - 1], "%Y-%m-%d").date()
        curr = datetime.strptime(study_dates[i], "%Y-%m-%d").date()
        if (curr - prev).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest


def get_most_productive_day():
    """
    Returns the day of the week with the most total study minutes.
    Returns (day_name, total_minutes) or (None, 0) if no sessions.
    """
    db = load_db()
    if not db["sessions"]:
        return None, 0

    day_totals = {}
    for s in db["sessions"]:
        day = datetime.strptime(s["date"], "%Y-%m-%d").strftime("%A")
        day_totals[day] = day_totals.get(day, 0) + s["duration_minutes"]

    best_day = max(day_totals, key=day_totals.get)
    return best_day, day_totals[best_day]


def get_most_productive_location():
    """
    Returns the location with the most total study minutes.
    Returns (location, total_minutes) or (None, 0) if no sessions.
    """
    db = load_db()
    sessions_with_location = [s for s in db["sessions"] if s.get("location")]
    if not sessions_with_location:
        return None, 0

    loc_totals = {}
    for s in sessions_with_location:
        loc = s["location"]
        loc_totals[loc] = loc_totals.get(loc, 0) + s["duration_minutes"]

    best = max(loc_totals, key=loc_totals.get)
    return best, loc_totals[best]


def get_minutes_by_session_type():
    """Returns {session_type: total_minutes}."""
    db = load_db()
    totals = {}
    for s in db["sessions"]:
        t = s["session_type"]
        totals[t] = totals.get(t, 0) + s["duration_minutes"]
    return totals


def get_mood_insights():
    """
    Returns a dict with mood analytics from sessions where both
    mood_before and mood_after were recorded.
    {
        avg_before: float or None,
        avg_after: float or None,
        improved: int,
        same: int,
        dropped: int,
        total_with_mood: int
    }
    """
    db = load_db()
    mood_sessions = [
        s for s in db["sessions"]
        if s.get("mood_before") is not None and s.get("mood_after") is not None
    ]

    if not mood_sessions:
        return {
            "avg_before": None,
            "avg_after": None,
            "improved": 0,
            "same": 0,
            "dropped": 0,
            "total_with_mood": 0
        }

    avg_before = sum(s["mood_before"] for s in mood_sessions) / len(mood_sessions)
    avg_after = sum(s["mood_after"] for s in mood_sessions) / len(mood_sessions)

    improved = sum(1 for s in mood_sessions if s["mood_after"] > s["mood_before"])
    same = sum(1 for s in mood_sessions if s["mood_after"] == s["mood_before"])
    dropped = sum(1 for s in mood_sessions if s["mood_after"] < s["mood_before"])

    return {
        "avg_before": round(avg_before, 1),
        "avg_after": round(avg_after, 1),
        "improved": improved,
        "same": same,
        "dropped": dropped,
        "total_with_mood": len(mood_sessions)
    }


def get_avg_rating_by_subject():
    """Returns {subject_id: avg_rating} for subjects with at least one rated session."""
    db = load_db()
    rated = {}
    counts = {}
    for s in db["sessions"]:
        if s.get("rating") is not None:
            sid = s["subject_id"]
            rated[sid] = rated.get(sid, 0) + s["rating"]
            counts[sid] = counts.get(sid, 0) + 1
    return {sid: round(rated[sid] / counts[sid], 1) for sid in rated}