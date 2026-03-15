# ui.py
# Responsible for: everything the user sees and types.
# Calls db.py for data. Calls models.py for validation and formatting.
# Never writes to the file system directly.

import os
from datetime import datetime

import db
import models

# ── navigation signals ────────────────────────────────────────────────────────
# These are returned by screens to tell the caller where to go next.
NAV_BACK = "NAV_BACK"   # go back one level
NAV_MAIN = "NAV_MAIN"   # go all the way to the main menu
NAV_QUIT = "NAV_QUIT"   # exit the app

# ── terminal helpers ──────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def line(char="─", width=55):
    print(char * width)


def header(title):
    clear()
    line("═")
    print(f"  {title}")
    line("═")
    print()


def pause(message="  Press Enter to continue..."):
    input(message)


def nav_hint():
    print("\n  .back · .main · .quit")


def handle_nav(raw):
    """
    Check if user typed a nav command.
    Returns NAV_BACK, NAV_MAIN, NAV_QUIT, or None.
    """
    if raw is None:
        return None
    stripped = raw.strip().lower()
    if stripped == ".quit":
        return NAV_QUIT
    if stripped == ".main":
        return NAV_MAIN
    if stripped == ".back":
        return NAV_BACK
    return None


def prompt(label, hint=""):
    """Single input line. hint shown in dim text if provided."""
    if hint:
        return input(f"  {label} ({hint}): ").strip()
    return input(f"  {label}: ").strip()


# ── pickers ───────────────────────────────────────────────────────────────────

def pick_from_list(options, label="Choose", allow_custom=False, default=None):
    """
    Displays a numbered list. User picks by number, types custom text,
    or presses Enter for the default.

    Returns (chosen_string, None) or (None, NAV_*).
    """
    print()
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    if allow_custom:
        print(f"  {len(options) + 1}. Other (type your own)")

    if default:
        hint = f"Enter for '{default}'"
    else:
        hint = "number"

    print()
    raw = input(f"  {label} ({hint}): ").strip()

    # nav check
    nav = handle_nav(raw)
    if nav:
        return None, nav

    # Enter — use default
    if raw == "" and default:
        return default, None

    # custom text option
    if allow_custom and raw == str(len(options) + 1):
        custom = input("  Enter custom type: ").strip()
        nav = handle_nav(custom)
        if nav:
            return None, nav
        if not custom:
            print("  Cannot be empty.")
            return pick_from_list(options, label, allow_custom, default)
        return custom, None

    # number pick
    try:
        index = int(raw) - 1
        if 0 <= index < len(options):
            return options[index], None
        else:
            print("  Invalid choice. Try again.")
            return pick_from_list(options, label, allow_custom, default)
    except ValueError:
        # user typed free text — treat as custom if allow_custom, else re-prompt
        if allow_custom and raw:
            return raw, None
        print("  Invalid choice. Try again.")
        return pick_from_list(options, label, allow_custom, default)


def pick_subject(prompt_label="Select subject"):
    """
    Shows active subjects as a numbered list.
    Returns (subject_dict, None) or (None, NAV_*).
    """
    subjects = db.get_all_subjects()
    if not subjects:
        print("\n  No subjects yet. Add one first.")
        pause()
        return None, NAV_BACK

    print()
    for i, s in enumerate(subjects, 1):
        print(f"  {i}. {s['name']}  [{s['default_type']}]")

    print()
    raw = input(f"  {prompt_label} (number): ").strip()

    nav = handle_nav(raw)
    if nav:
        return None, nav

    try:
        index = int(raw) - 1
        if 0 <= index < len(subjects):
            return subjects[index], None
        else:
            print("  Invalid choice.")
            return pick_subject(prompt_label)
    except ValueError:
        print("  Please enter a number.")
        return pick_subject(prompt_label)


# ── home screen ───────────────────────────────────────────────────────────────

def screen_home():
    """
    Displays today's summary, streak, week total, subject highlights, alerts.
    Returns a nav signal or None (to show main menu).
    """
    header("📚  STUDY SESSION TRACKER")

    today = datetime.now().strftime("%Y-%m-%d")
    today_sessions = db.get_sessions_by_date(today)
    today_minutes = sum(s["duration_minutes"] for s in today_sessions)

    # ── TODAY ─────────────────────────────────────────────────────────────────
    print("  TODAY")
    line()
    if today_sessions:
        print(f"  Sessions logged : {len(today_sessions)}")
        print(f"  Time studied    : {models.format_duration(today_minutes)}")
    else:
        print("  No sessions logged today yet.")
    print()

    # ── STREAK ───────────────────────────────────────────────────────────────
    streak = db.get_streak()
    print("  STREAK")
    line()
    if streak == 0:
        print("  No active streak. Log a session to start one.")
    elif streak == 1:
        print(f"  🔥 {streak} day streak — keep it going!")
    else:
        print(f"  🔥 {streak} day streak — great consistency!")
    print()

    # ── THIS WEEK ─────────────────────────────────────────────────────────────
    from datetime import date, timedelta
    today_date = date.today()
    week_start = (today_date - timedelta(days=today_date.weekday())).isoformat()
    week_end = today_date.isoformat()
    week_sessions = db.get_sessions_in_date_range(week_start, week_end)
    week_minutes = sum(s["duration_minutes"] for s in week_sessions)

    last_week_start = (today_date - timedelta(days=today_date.weekday() + 7)).isoformat()
    last_week_end = (today_date - timedelta(days=today_date.weekday() + 1)).isoformat()
    last_week_sessions = db.get_sessions_in_date_range(last_week_start, last_week_end)
    last_week_minutes = sum(s["duration_minutes"] for s in last_week_sessions)

    print("  THIS WEEK")
    line()
    print(f"  Time studied : {models.format_duration(week_minutes)}")
    if last_week_minutes > 0:
        diff = week_minutes - last_week_minutes
        direction = "+" if diff >= 0 else ""
        print(f"  vs last week : {direction}{models.format_duration(abs(diff))} "
              f"({'up' if diff >= 0 else 'down'})")
    print()

    # ── SUBJECTS ──────────────────────────────────────────────────────────────
    totals = db.get_total_minutes_by_subject()
    subjects = db.get_all_subjects()

    if totals and subjects:
        print("  SUBJECTS")
        line()
        # match ids to names
        named = []
        for s in subjects:
            mins = totals.get(s["id"], 0)
            named.append((s["name"], mins))
        named.sort(key=lambda x: x[1], reverse=True)

        if named:
            print(f"  Most studied  : {named[0][0]} ({models.format_duration(named[0][1])})")
        if len(named) > 1 and named[-1][1] > 0:
            print(f"  Least studied : {named[-1][0]} ({models.format_duration(named[-1][1])})")
        print()

    # ── ALERTS ────────────────────────────────────────────────────────────────
    all_sessions = db.get_all_sessions()
    alerts = []

    if not all_sessions:
        alerts.append("No sessions logged yet. Start by adding a subject.")
    elif streak == 0:
        alerts.append("You haven't studied today or yesterday. Streak at risk.")

    if alerts:
        print("  ALERTS")
        line()
        for alert in alerts:
            print(f"  ⚠  {alert}")
        print()


# ── subject screens ───────────────────────────────────────────────────────────

def screen_add_subject():
    header("ADD SUBJECT")
    nav_hint()
    print()

    # name
    name = prompt("Subject name", "e.g. CSCI 201, React Hooks, Spanish B2")
    nav = handle_nav(name)
    if nav:
        return nav
    if not name:
        print("  Name cannot be empty.")
        pause()
        return NAV_BACK

    # default type
    print("\n  Default session type:")
    session_type, nav = pick_from_list(
        models.SESSION_TYPES,
        label="Type",
        allow_custom=True
    )
    if nav:
        return nav

    subject, err = db.create_subject(name, session_type)
    if err:
        print(f"\n  ✗ {err}")
        pause()
        return NAV_BACK

    print(f"\n  ✓ Subject '{subject['name']}' added.")
    pause()
    return NAV_BACK


def screen_view_subjects():
    header("MY SUBJECTS")
    nav_hint()

    subjects = db.get_all_subjects()
    if not subjects:
        print("  No subjects yet.")
        pause()
        return NAV_BACK

    totals = db.get_total_minutes_by_subject()
    print()
    for s in subjects:
        total = totals.get(s["id"], 0)
        print(f"  {s['name']}")
        print(f"    Type     : {s['default_type']}")
        print(f"    Total    : {models.format_duration(total)}")
        print(f"    Added    : {models.format_date_display(s['created_date'][:10])}")
        line("·")

    pause()
    return NAV_BACK


def screen_archive_subject():
    header("ARCHIVE SUBJECT")
    nav_hint()
    print()

    subject, nav = pick_subject("Subject to archive")
    if nav:
        return nav

    confirm = input(f"\n  Archive '{subject['name']}'? (y/n): ").strip().lower()
    if confirm == "y":
        db.archive_subject(subject["id"])
        print(f"  ✓ '{subject['name']}' archived.")
    else:
        print("  Cancelled.")

    pause()
    return NAV_BACK


# ── session screens ───────────────────────────────────────────────────────────

def screen_log_session():
    header("LOG SESSION")
    nav_hint()
    print()

    # pick subject
    subject, nav = pick_subject()
    if nav:
        return nav

    print(f"\n  Subject: {subject['name']}")
    line("·")

    # session type — default from subject, override allowed
    print(f"\n  Session type  (default: {subject['default_type']}):")
    session_type, nav = pick_from_list(
        models.SESSION_TYPES,
        label="Type",
        allow_custom=True,
        default=subject["default_type"]
    )
    if nav:
        return nav

    # duration
    while True:
        raw = prompt("Duration in minutes", "e.g. 60")
        nav = handle_nav(raw)
        if nav:
            return nav
        duration, err = models.validate_duration(raw)
        if err:
            print(f"  ✗ {err}")
        else:
            break

    # date
    while True:
        raw = prompt("Date", "YYYY-MM-DD or Enter for today")
        nav = handle_nav(raw)
        if nav:
            return nav
        date_str, err = models.validate_date(raw)
        if err:
            print(f"  ✗ {err}")
        else:
            break

    # location
    print("\n  Location:")
    location, nav = pick_from_list(
        models.LOCATIONS,
        label="Location",
        default="Home"
    )
    if nav:
        return nav

    # rating
    while True:
        raw = prompt("Focus rating 1-5", "Enter to skip")
        nav = handle_nav(raw)
        if nav:
            return nav
        rating, err = models.validate_rating(raw)
        if err:
            print(f"  ✗ {err}")
        else:
            break

    # mood before
    while True:
        raw = prompt("Mood before (1-5)", "Enter to skip")
        nav = handle_nav(raw)
        if nav:
            return nav
        mood_before, err = models.validate_mood(raw, "Mood before")
        if err:
            print(f"  ✗ {err}")
        else:
            break

    # mood after
    while True:
        raw = prompt("Mood after (1-5)", "Enter to skip")
        nav = handle_nav(raw)
        if nav:
            return nav
        mood_after, err = models.validate_mood(raw, "Mood after")
        if err:
            print(f"  ✗ {err}")
        else:
            break

    # notes
    notes = prompt("Notes", "Enter to skip")
    nav = handle_nav(notes)
    if nav:
        return nav
    if not notes:
        notes = None

    # save
    session, err = db.create_session(
        subject["id"], session_type, duration, date_str,
        location, rating, mood_before, mood_after, notes
    )

    if err:
        print(f"\n  ✗ {err}")
        pause()
        return NAV_BACK

    print(f"\n  ✓ Session logged — {models.format_duration(duration)} of {subject['name']}.")
    pause()
    return NAV_BACK


def screen_view_sessions():
    header("SESSION HISTORY")
    nav_hint()
    print()

    subjects = db.get_all_subjects(include_archived=True)
    if not subjects:
        print("  No subjects yet.")
        pause()
        return NAV_BACK

    # let user filter by subject or see all
    print("  View sessions for:")
    print("  1. All subjects")
    for i, s in enumerate(subjects, 2):
        label = s["name"] + (" [archived]" if s["archived"] else "")
        print(f"  {i}. {label}")

    print()
    raw = input("  Choice (number): ").strip()
    nav = handle_nav(raw)
    if nav:
        return nav

    try:
        choice = int(raw)
    except ValueError:
        print("  Invalid choice.")
        pause()
        return NAV_BACK

    if choice == 1:
        sessions = db.get_all_sessions()
        title = "All Sessions"
    elif 2 <= choice <= len(subjects) + 1:
        selected = subjects[choice - 2]
        sessions = db.get_sessions_by_subject(selected["id"])
        title = selected["name"]
    else:
        print("  Invalid choice.")
        pause()
        return NAV_BACK

    if not sessions:
        print(f"\n  No sessions found for {title}.")
        pause()
        return NAV_BACK

    # sort newest first
    sessions = sorted(sessions, key=lambda s: s["date"], reverse=True)

    # build subject id → name lookup
    subject_map = {s["id"]: s["name"] for s in db.get_all_subjects(include_archived=True)}

    print(f"\n  {title}  ({len(sessions)} session{'s' if len(sessions) != 1 else ''})\n")
    line()

    for s in sessions:
        sub_name = subject_map.get(s["subject_id"], "Unknown")
        print(f"  {models.format_date_display(s['date'])}  ·  {sub_name}")
        print(f"    Type     : {s['session_type']}")
        print(f"    Duration : {models.format_duration(s['duration_minutes'])}")
        print(f"    Location : {s['location'] or '—'}")
        print(f"    Rating   : {models.stars(s['rating'])}")
        print(f"    Mood     : {models.mood_label(s['mood_before'])} → {models.mood_label(s['mood_after'])}")
        if s["notes"]:
            print(f"    Notes    : {s['notes']}")
        line("·")

    pause()
    return NAV_BACK


# ── subjects menu ─────────────────────────────────────────────────────────────

def menu_subjects():
    while True:
        header("SUBJECTS")
        nav_hint()
        print()
        print("  1. View all subjects")
        print("  2. Add subject")
        print("  3. Archive subject")
        print()

        raw = input("  Choice: ").strip()
        nav = handle_nav(raw)
        if nav:
            return nav

        if raw == "1":
            result = screen_view_subjects()
        elif raw == "2":
            result = screen_add_subject()
        elif raw == "3":
            result = screen_archive_subject()
        else:
            continue

        if result == NAV_QUIT:
            return NAV_QUIT
        if result == NAV_MAIN:
            return NAV_MAIN
        # NAV_BACK just loops back to this menu


# ── sessions menu ─────────────────────────────────────────────────────────────

def menu_sessions():
    while True:
        header("SESSIONS")
        nav_hint()
        print()
        print("  1. Log a session")
        print("  2. View session history")
        print()

        raw = input("  Choice: ").strip()
        nav = handle_nav(raw)
        if nav:
            return nav

        if raw == "1":
            result = screen_log_session()
        elif raw == "2":
            result = screen_view_sessions()
        else:
            continue

        if result == NAV_QUIT:
            return NAV_QUIT
        if result == NAV_MAIN:
            return NAV_MAIN
