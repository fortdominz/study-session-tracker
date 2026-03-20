# ui.py
# Responsible for: everything the user sees and types.
# Calls db.py for data. Calls models.py for validation and formatting.
# Never writes to the file system directly.

import os
from datetime import datetime, date, timedelta

import db
import models

# ── navigation signals ────────────────────────────────────────────────────────
NAV_BACK = "NAV_BACK"
NAV_MAIN = "NAV_MAIN"
NAV_QUIT = "NAV_QUIT"

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
    print("  .back · .main · .quit")
    print()


def handle_nav(raw):
    """Check if user typed a nav command. Returns signal or None."""
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
    """Single input line with optional hint."""
    if hint:
        return input(f"  {label} ({hint}): ").strip()
    return input(f"  {label}: ").strip()


# ── pickers ───────────────────────────────────────────────────────────────────

def pick_from_list(options, label="Choose", allow_custom=False, default=None):
    """
    Numbered list picker. User picks by number, types custom,
    or presses Enter for default.
    Returns (chosen_string, None) or (None, NAV_*).
    """
    print()
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    if allow_custom:
        print(f"  {len(options) + 1}. Other (type your own)")

    hint = f"Enter for '{default}'" if default else "number"
    print()
    raw = input(f"  {label} ({hint}): ").strip()

    nav = handle_nav(raw)
    if nav:
        return None, nav

    if raw == "" and default:
        return default, None

    if allow_custom and raw == str(len(options) + 1):
        custom = input("  Enter custom type: ").strip()
        nav = handle_nav(custom)
        if nav:
            return None, nav
        if not custom:
            print("  Cannot be empty.")
            return pick_from_list(options, label, allow_custom, default)
        return custom, None

    try:
        index = int(raw) - 1
        if 0 <= index < len(options):
            return options[index], None
        else:
            print("  Invalid choice. Try again.")
            return pick_from_list(options, label, allow_custom, default)
    except ValueError:
        if allow_custom and raw:
            return raw, None
        print("  Invalid choice. Try again.")
        return pick_from_list(options, label, allow_custom, default)


# ── home screen ───────────────────────────────────────────────────────────────

def screen_home():
    """
    Shows today's summary, streak, week total, topic highlights, alerts.
    If no topics exist, shows a first-time welcome instead.
    """
    header("📚  STUDY SESSION TRACKER")

    subjects = db.get_all_subjects()

    # ── first time user ───────────────────────────────────────────────────────
    if not subjects:
        print("  Welcome! Let's get you set up.")
        print()
        print("  You don't have any topics yet.")
        print("  A topic is anything you study — a course, a skill,")
        print("  a language, a project. Start by adding one.")
        print()
        return

    # ── returning user ────────────────────────────────────────────────────────
    today = datetime.now().strftime("%Y-%m-%d")
    today_sessions = db.get_sessions_by_date(today)
    today_minutes = sum(s["duration_minutes"] for s in today_sessions)

    # TODAY
    print("  TODAY")
    line()
    if today_sessions:
        print(f"  Sessions logged : {len(today_sessions)}")
        print(f"  Time studied    : {models.format_duration(today_minutes)}")
    else:
        print("  No sessions logged today yet.")
    print()

    # STREAK
    streak = db.get_streak()
    print("  STREAK")
    line()
    if streak == 0:
        print("  No active streak. Log a session to start one.")
    elif streak == 1:
        print(f"  🔥 {streak} day — keep it going!")
    else:
        print(f"  🔥 {streak} days — great consistency!")
    print()

    # THIS WEEK
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
        direction = "+" if diff >= 0 else "-"
        print(f"  vs last week : {direction}{models.format_duration(abs(diff))} "
              f"({'up' if diff >= 0 else 'down'})")
    print()

    # TOPICS — only show if any sessions have been logged
    totals = db.get_total_minutes_by_subject()
    if any(v > 0 for v in totals.values()):
        print("  TOPICS")
        line()
        named = [(s["name"], totals.get(s["id"], 0)) for s in subjects]
        named.sort(key=lambda x: x[1], reverse=True)
        print(f"  Most studied  : {named[0][0]} ({models.format_duration(named[0][1])})")
        if len(named) > 1 and named[-1][1] > 0:
            print(f"  Least studied : {named[-1][0]} ({models.format_duration(named[-1][1])})")
        print()

    # ALERTS
    all_sessions = db.get_all_sessions()
    alerts = []
    if not all_sessions:
        alerts.append("No sessions logged yet. Log your first session.")
    elif streak == 0:
        alerts.append("You haven't studied today or yesterday. Streak at risk.")

    if alerts:
        print("  ALERTS")
        line()
        for alert in alerts:
            print(f"  ⚠  {alert}")
        print()


# ── topic screens ─────────────────────────────────────────────────────────────

def screen_add_topic():
    header("ADD A TOPIC")
    nav_hint()
    print("  A topic is anything you study — a course, a skill,")
    print("  a language, a personal project, anything.")
    print()

    name = prompt("Topic name", "e.g. CSCI 201, React, Spanish, DSA")
    nav = handle_nav(name)
    if nav:
        return nav
    if not name:
        print("  Name cannot be empty.")
        pause()
        return NAV_BACK

    print("\n  What kind of studying do you usually do for this topic?")
    print("  This becomes the default — you can always change it per session.")
    session_type, nav = pick_from_list(
        models.SESSION_TYPES,
        label="Type",
        allow_custom=True
    )
    if nav:
        return nav

    topic, err = db.create_subject(name, session_type)
    if err:
        print(f"\n  ✗ {err}")
        pause()
        return NAV_BACK

    print(f"\n  ✓ '{topic['name']}' added as a {session_type} topic.")
    print("  You can now log sessions under it.")
    pause()
    return NAV_BACK


def screen_edit_topic():
    header("EDIT A TOPIC")
    nav_hint()

    subjects = db.get_all_subjects()
    if not subjects:
        print("  No active topics to edit.")
        pause()
        return NAV_BACK

    for i, s in enumerate(subjects, 1):
        print(f"  {i}. {s['name']}  [{s['default_type']}]")

    print()
    raw = input("  Topic to edit (number): ").strip()
    nav = handle_nav(raw)
    if nav:
        return nav

    try:
        index = int(raw) - 1
        if not (0 <= index < len(subjects)):
            print("  Invalid choice.")
            pause()
            return NAV_BACK
    except ValueError:
        print("  Please enter a number.")
        pause()
        return NAV_BACK

    selected = subjects[index]

    # what to edit
    print(f"\n  Editing: {selected['name']}")
    line("·")
    print("  1. Rename topic")
    print("  2. Change default session type")
    print("  3. Both")
    print()

    raw = input("  Choice: ").strip()
    nav = handle_nav(raw)
    if nav:
        return nav

    updates = {}

    if raw in ("1", "3"):
        new_name = prompt("New name", f"Enter for '{selected['name']}'")
        nav = handle_nav(new_name)
        if nav:
            return nav
        if new_name:
            updates["name"] = new_name

    if raw in ("2", "3"):
        print("\n  New default session type:")
        new_type, nav = pick_from_list(
            models.SESSION_TYPES,
            label="Type",
            allow_custom=True,
            default=selected["default_type"]
        )
        if nav:
            return nav
        updates["default_type"] = new_type

    if not updates:
        print("  Nothing changed.")
        pause()
        return NAV_BACK

    updated, err = db.update_subject(selected["id"], updates)
    if err:
        print(f"\n  ✗ {err}")
        pause()
        return NAV_BACK

    print(f"\n  ✓ Topic updated.")
    pause()
    return NAV_BACK


def screen_view_topics():
    header("MY TOPICS")
    nav_hint()

    subjects = db.get_all_subjects()
    if not subjects:
        print("  No topics yet. Add one from the main menu.")
        pause()
        return NAV_BACK

    totals = db.get_total_minutes_by_subject()
    for s in subjects:
        total = totals.get(s["id"], 0)
        sessions = db.get_sessions_by_subject(s["id"])
        print(f"  {s['name']}")
        print(f"    Default type : {s['default_type']}")
        print(f"    Total time   : {models.format_duration(total)}")
        print(f"    Sessions     : {len(sessions)}")
        print(f"    Added        : {models.format_date_display(s['created_date'][:10])}")
        line("·")

    pause()
    return NAV_BACK


def screen_archive_topic():
    header("ARCHIVE A TOPIC")
    nav_hint()
    print("  Archiving hides a topic from session logging.")
    print("  Your past sessions under it are kept.")
    print()

    subjects = db.get_all_subjects()
    if not subjects:
        print("  No active topics to archive.")
        pause()
        return NAV_BACK

    for i, s in enumerate(subjects, 1):
        print(f"  {i}. {s['name']}  [{s['default_type']}]")

    print()
    raw = input("  Topic to archive (number): ").strip()
    nav = handle_nav(raw)
    if nav:
        return nav

    try:
        index = int(raw) - 1
        if not (0 <= index < len(subjects)):
            print("  Invalid choice.")
            pause()
            return NAV_BACK
    except ValueError:
        print("  Please enter a number.")
        pause()
        return NAV_BACK

    selected = subjects[index]
    confirm = input(f"\n  Archive '{selected['name']}'? (y/n): ").strip().lower()
    nav = handle_nav(confirm)
    if nav:
        return nav

    if confirm == "y":
        db.archive_subject(selected["id"])
        print(f"\n  ✓ '{selected['name']}' archived.")
    else:
        print("\n  Cancelled.")

    pause()
    return NAV_BACK


# ── log session screen ────────────────────────────────────────────────────────

def screen_log_session():
    """
    Walks the user through logging a session step by step.
    If no topics exist, offers to add one first inline.
    """
    header("LOG A SESSION")
    nav_hint()

    # guard — no topics yet
    subjects = db.get_all_subjects()
    if not subjects:
        print("  You don't have any topics yet.")
        print("  Add a topic first so you can log sessions under it.")
        print()
        raw = input("  Add a topic now? (y/n): ").strip().lower()
        nav = handle_nav(raw)
        if nav:
            return nav
        if raw == "y":
            result = screen_add_topic()
            if result in (NAV_QUIT, NAV_MAIN):
                return result
            subjects = db.get_all_subjects()
            if not subjects:
                return NAV_BACK
        else:
            return NAV_BACK

    # step 1 — pick topic
    print("  What did you study?")
    print()
    for i, s in enumerate(subjects, 1):
        print(f"  {i}. {s['name']}  [{s['default_type']}]")
    print(f"  {len(subjects) + 1}. + Add a new topic")
    print()

    raw = input("  Choose (number): ").strip()
    nav = handle_nav(raw)
    if nav:
        return nav

    try:
        choice = int(raw)
    except ValueError:
        print("  Please enter a number.")
        pause()
        return NAV_BACK

    if choice == len(subjects) + 1:
        result = screen_add_topic()
        if result in (NAV_QUIT, NAV_MAIN):
            return result
        subjects = db.get_all_subjects()
        if not subjects:
            return NAV_BACK
        subject = subjects[-1]
    elif 1 <= choice <= len(subjects):
        subject = subjects[choice - 1]
    else:
        print("  Invalid choice.")
        pause()
        return NAV_BACK

    print(f"\n  Topic: {subject['name']}")
    line("·")

    # step 2 — session type
    print(f"\n  What kind of session is this?")
    print(f"  Default for this topic: {subject['default_type']}")
    session_type, nav = pick_from_list(
        models.SESSION_TYPES,
        label="Type",
        allow_custom=True,
        default=subject["default_type"]
    )
    if nav:
        return nav

    # step 3 — duration
    print()
    while True:
        raw = prompt("How long did you study?", "minutes, e.g. 60")
        nav = handle_nav(raw)
        if nav:
            return nav
        duration, err = models.validate_duration(raw)
        if err:
            print(f"  ✗ {err}")
        else:
            break

    # step 4 — date
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

    # step 5 — location
    print("\n  Where did you study?")
    location, nav = pick_from_list(
        models.LOCATIONS,
        label="Location",
        default="Home"
    )
    if nav:
        return nav

    # step 6 — focus rating
    print()
    while True:
        raw = prompt("How focused were you? (1-5)", "Enter to skip")
        nav = handle_nav(raw)
        if nav:
            return nav
        rating, err = models.validate_rating(raw)
        if err:
            print(f"  ✗ {err}")
        else:
            break

    # step 7 — mood before
    while True:
        raw = prompt("Mood before studying (1-5)", "Enter to skip")
        nav = handle_nav(raw)
        if nav:
            return nav
        mood_before, err = models.validate_mood(raw, "Mood before")
        if err:
            print(f"  ✗ {err}")
        else:
            break

    # step 8 — mood after
    while True:
        raw = prompt("Mood after studying (1-5)", "Enter to skip")
        nav = handle_nav(raw)
        if nav:
            return nav
        mood_after, err = models.validate_mood(raw, "Mood after")
        if err:
            print(f"  ✗ {err}")
        else:
            break

    # step 9 — notes
    notes = prompt("Any notes?", "Enter to skip")
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

    print(f"\n  ✓ Session logged.")
    print(f"    {subject['name']}  ·  {models.format_duration(duration)}  ·  {models.format_date_display(date_str)}")
    pause()
    return NAV_BACK


# ── edit session screen ───────────────────────────────────────────────────────

def screen_edit_session():
    header("EDIT A SESSION")
    nav_hint()

    all_subjects = db.get_all_subjects(include_archived=True)
    sessions = db.get_all_sessions()

    if not sessions:
        print("  No sessions logged yet.")
        pause()
        return NAV_BACK

    # show sessions — newest first
    subject_map = {s["id"]: s["name"] for s in all_subjects}
    sessions_sorted = sorted(sessions, key=lambda s: s["date"], reverse=True)

    # show last 10 to keep the list manageable
    display = sessions_sorted[:10]
    print("  Which session do you want to edit?")
    print()
    for i, s in enumerate(display, 1):
        sub_name = subject_map.get(s["subject_id"], "Unknown")
        print(f"  {i}. {models.format_date_display(s['date'])}  ·  {sub_name}  ·  {models.format_duration(s['duration_minutes'])}")

    print()
    raw = input("  Choose (number): ").strip()
    nav = handle_nav(raw)
    if nav:
        return nav

    try:
        index = int(raw) - 1
        if not (0 <= index < len(display)):
            print("  Invalid choice.")
            pause()
            return NAV_BACK
    except ValueError:
        print("  Please enter a number.")
        pause()
        return NAV_BACK

    session = display[index]
    sub_name = subject_map.get(session["subject_id"], "Unknown")

    # show current values and let user pick what to edit
    print(f"\n  Session: {models.format_date_display(session['date'])}  ·  {sub_name}")
    line("·")
    print(f"  1. Duration    [{models.format_duration(session['duration_minutes'])}]")
    print(f"  2. Date        [{models.format_date_display(session['date'])}]")
    print(f"  3. Type        [{session['session_type']}]")
    print(f"  4. Location    [{session['location'] or '—'}]")
    print(f"  5. Focus       [{models.stars(session['rating'])}]")
    print(f"  6. Mood before [{models.mood_label(session['mood_before'])}]")
    print(f"  7. Mood after  [{models.mood_label(session['mood_after'])}]")
    print(f"  8. Notes       [{session['notes'] or '—'}]")
    print()

    raw = input("  Field to edit (number): ").strip()
    nav = handle_nav(raw)
    if nav:
        return nav

    updates = {}

    if raw == "1":
        while True:
            val = prompt("New duration", "minutes")
            nav = handle_nav(val)
            if nav:
                return nav
            duration, err = models.validate_duration(val)
            if err:
                print(f"  ✗ {err}")
            else:
                updates["duration_minutes"] = duration
                break

    elif raw == "2":
        while True:
            val = prompt("New date", "YYYY-MM-DD")
            nav = handle_nav(val)
            if nav:
                return nav
            date_str, err = models.validate_date(val)
            if err:
                print(f"  ✗ {err}")
            else:
                updates["date"] = date_str
                break

    elif raw == "3":
        print("\n  New session type:")
        new_type, nav = pick_from_list(
            models.SESSION_TYPES,
            label="Type",
            allow_custom=True,
            default=session["session_type"]
        )
        if nav:
            return nav
        updates["session_type"] = new_type

    elif raw == "4":
        print("\n  New location:")
        new_loc, nav = pick_from_list(
            models.LOCATIONS,
            label="Location",
            default=session["location"] or "Home"
        )
        if nav:
            return nav
        updates["location"] = new_loc

    elif raw == "5":
        while True:
            val = prompt("New focus rating (1-5)", "Enter to clear")
            nav = handle_nav(val)
            if nav:
                return nav
            rating, err = models.validate_rating(val)
            if err:
                print(f"  ✗ {err}")
            else:
                updates["rating"] = rating
                break

    elif raw == "6":
        while True:
            val = prompt("New mood before (1-5)", "Enter to clear")
            nav = handle_nav(val)
            if nav:
                return nav
            mood, err = models.validate_mood(val, "Mood before")
            if err:
                print(f"  ✗ {err}")
            else:
                updates["mood_before"] = mood
                break

    elif raw == "7":
        while True:
            val = prompt("New mood after (1-5)", "Enter to clear")
            nav = handle_nav(val)
            if nav:
                return nav
            mood, err = models.validate_mood(val, "Mood after")
            if err:
                print(f"  ✗ {err}")
            else:
                updates["mood_after"] = mood
                break

    elif raw == "8":
        val = prompt("New notes", "Enter to clear")
        nav = handle_nav(val)
        if nav:
            return nav
        updates["notes"] = val if val else None

    else:
        print("  Invalid choice.")
        pause()
        return NAV_BACK

    updated, err = db.update_session(session["id"], updates)
    if err:
        print(f"\n  ✗ {err}")
        pause()
        return NAV_BACK

    print(f"\n  ✓ Session updated.")
    pause()
    return NAV_BACK


# ── delete session screen ─────────────────────────────────────────────────────

def screen_delete_session():
    header("DELETE A SESSION")
    nav_hint()

    all_subjects = db.get_all_subjects(include_archived=True)
    sessions = db.get_all_sessions()

    if not sessions:
        print("  No sessions logged yet.")
        pause()
        return NAV_BACK

    subject_map = {s["id"]: s["name"] for s in all_subjects}
    sessions_sorted = sorted(sessions, key=lambda s: s["date"], reverse=True)
    display = sessions_sorted[:10]

    print("  Which session do you want to delete?")
    print()
    for i, s in enumerate(display, 1):
        sub_name = subject_map.get(s["subject_id"], "Unknown")
        print(f"  {i}. {models.format_date_display(s['date'])}  ·  {sub_name}  ·  {models.format_duration(s['duration_minutes'])}")

    print()
    raw = input("  Choose (number): ").strip()
    nav = handle_nav(raw)
    if nav:
        return nav

    try:
        index = int(raw) - 1
        if not (0 <= index < len(display)):
            print("  Invalid choice.")
            pause()
            return NAV_BACK
    except ValueError:
        print("  Please enter a number.")
        pause()
        return NAV_BACK

    session = display[index]
    sub_name = subject_map.get(session["subject_id"], "Unknown")

    print(f"\n  {models.format_date_display(session['date'])}  ·  {sub_name}  ·  {models.format_duration(session['duration_minutes'])}")
    confirm = input("\n  Delete this session? This cannot be undone. (y/n): ").strip().lower()
    nav = handle_nav(confirm)
    if nav:
        return nav

    if confirm == "y":
        _, err = db.delete_session(session["id"])
        if err:
            print(f"\n  ✗ {err}")
        else:
            print(f"\n  ✓ Session deleted.")
    else:
        print("\n  Cancelled.")

    pause()
    return NAV_BACK


# ── view sessions screen ──────────────────────────────────────────────────────

def screen_view_sessions():
    header("MY SESSIONS")
    nav_hint()

    all_subjects = db.get_all_subjects(include_archived=True)
    if not all_subjects:
        print("  No topics or sessions yet.")
        pause()
        return NAV_BACK

    print("  View sessions for:")
    print("  1. All topics")
    for i, s in enumerate(all_subjects, 2):
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
        title = "All Topics"
    elif 2 <= choice <= len(all_subjects) + 1:
        selected = all_subjects[choice - 2]
        sessions = db.get_sessions_by_subject(selected["id"])
        title = selected["name"]
    else:
        print("  Invalid choice.")
        pause()
        return NAV_BACK

    if not sessions:
        print(f"\n  No sessions found.")
        pause()
        return NAV_BACK

    sessions = sorted(sessions, key=lambda s: s["date"], reverse=True)
    subject_map = {s["id"]: s["name"] for s in all_subjects}

    print(f"\n  {title}  —  {len(sessions)} session{'s' if len(sessions) != 1 else ''}\n")
    line()

    for s in sessions:
        sub_name = subject_map.get(s["subject_id"], "Unknown")
        print(f"  {models.format_date_display(s['date'])}  ·  {sub_name}")
        print(f"    Type     : {s['session_type']}")
        print(f"    Duration : {models.format_duration(s['duration_minutes'])}")
        print(f"    Location : {s['location'] or '—'}")
        print(f"    Focus    : {models.stars(s['rating'])}")
        print(f"    Mood     : {models.mood_label(s['mood_before'])} → {models.mood_label(s['mood_after'])}")
        if s["notes"]:
            print(f"    Notes    : {s['notes']}")
        line("·")

    pause()
    return NAV_BACK


# ── my topics menu ────────────────────────────────────────────────────────────

def menu_my_topics():
    while True:
        header("MY TOPICS")
        nav_hint()
        print("  1. View all topics       — see your topics and total time")
        print("  2. Add a topic           — add something new you study")
        print("  3. Edit a topic          — rename or change default type")
        print("  4. Archive a topic       — hide a topic you no longer study")
        print()

        raw = input("  Choice: ").strip()
        nav = handle_nav(raw)
        if nav:
            return nav

        if raw == "1":
            result = screen_view_topics()
        elif raw == "2":
            result = screen_add_topic()
        elif raw == "3":
            result = screen_edit_topic()
        elif raw == "4":
            result = screen_archive_topic()
        else:
            continue

        if result == NAV_QUIT:
            return NAV_QUIT
        if result == NAV_MAIN:
            return NAV_MAIN


# ── my sessions menu ──────────────────────────────────────────────────────────

def menu_my_sessions():
    while True:
        header("MY SESSIONS")
        nav_hint()
        print("  1. View session history  — browse past sessions by topic")
        print("  2. Edit a session        — update a field on a past session")
        print("  3. Delete a session      — remove a session permanently")
        print()

        raw = input("  Choice: ").strip()
        nav = handle_nav(raw)
        if nav:
            return nav

        if raw == "1":
            result = screen_view_sessions()
        elif raw == "2":
            result = screen_edit_session()
        elif raw == "3":
            result = screen_delete_session()
        else:
            continue

        if result == NAV_QUIT:
            return NAV_QUIT
        if result == NAV_MAIN:
            return NAV_MAIN