# Study Session Tracker

A Python CLI application for logging and analyzing study sessions across multiple topics. Track duration, focus rating, mood, streaks, and patterns — all from the terminal.

Built with zero external libraries. Part of the [dominioneze.com](https://dominioneze.com) project suite.

---

## Demo

[▶ Watch the demo](https://youtu.be/PLACEHOLDER)

---

## Features

**Topics**
- Add topics for anything you study — courses, skills, languages, projects
- Each topic has a default session type (Course, Self-Study, Research, Practice, or custom)
- Archive topics you no longer study — history is preserved
- Restore archived topics at any time

**Session Logging**
- Guided step-by-step flow — topic, type, duration, date, location, rating, mood, notes
- Add a new topic inline during logging without backing out
- Skip optional fields with Enter — mood, rating, and notes are never required
- Session type defaults to your topic's setting, overridable per session

**Session History**
- View all sessions or filter by topic
- Sort by date, duration, focus rating, topic name, or session type
- Edit any field on a past session
- Delete sessions — permanently logged in deleted session history
- Deleted session history — read-only, persists forever

**Analytics**
- Overall stats — total sessions, total time, average and longest session
- By topic — time per topic ranked, average focus rating
- By session type — terminal bar chart, color-coded
- Streaks — current streak, longest streak ever, most productive day and location
- Mood insights — average before/after, delta, improved/same/dropped breakdown

**Export**
- Export all sessions or filter by topic to a CSV file
- Auto-generated filename with date stamp, or choose your own

---

## Getting Started

```bash
git clone https://github.com/fortdominz/study-session-tracker
cd study-session-tracker
python main.py
```

No installs. No dependencies. Just Python 3.

---

## Project Structure

```
study-session-tracker/
├── db.py        # Data layer — JSON storage, all CRUD, analytics helpers
├── models.py    # Validation, formatting, color constants
├── ui.py        # All screens and user input
└── main.py      # Entry point and main menu
```

**Separation of concerns:** `db.py` is the only file that touches storage. Swapping to MongoDB only requires changing `db.py`.

---

## Navigation

Type these at any prompt on any screen:

| Command | Action |
|---------|--------|
| `.back` | Go back one level |
| `.main` | Return to main menu |
| `.quit` | Exit the app |

---

## Data

Sessions are stored in `study_tracker.json` in the project folder. The file is created automatically on first run.

Deleted sessions and archived topic snapshots are stored permanently — nothing is ever fully erased.

---

## Part of a Larger System

This is the third of five CLI tools building toward **dominioneze.com** — a live full-stack personal platform.

| Project | Status |
|---------|--------|
| Job Application Tracker | ✅ Complete |
| DayKeep (Daily Life Tracker) | ✅ Complete |
| Study Session Tracker | ✅ Complete |
| MongoDB migration + FastAPI | ⏳ Planned |
| dominioneze.com (React + Tailwind) | ⏳ Planned |

---

*Dominion Eze · [github.com/fortdominz](https://github.com/fortdominz) · EzApp*
