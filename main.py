# main.py
# Entry point. Runs the main menu loop.
# Calls ui.py for all screens. Never touches db.py or models.py directly.

import ui
import db


def main():
    while True:
        ui.screen_home()

        has_topics = len(db.get_all_subjects()) > 0

        print("  MENU")
        ui.line()

        if not has_topics:
            # first time user — one option only
            print("  1. Add a Topic           — set up what you study")
            print("  2. Quit")
            print()
            raw = input("  Choice: ").strip()
            nav = ui.handle_nav(raw)
            if nav == ui.NAV_QUIT or raw == "2":
                break
            if raw == "1":
                result = ui.screen_add_topic()
                if result == ui.NAV_QUIT:
                    break

        else:
            # returning user — full menu
            print("  1. Add a Topic           — set up what you study")
            print("  2. Log a Session         — track a new study session")
            print("  3. My Sessions           — view, edit, delete sessions")
            print("  4. My Topics             — add, view, edit, archive topics")
            print("  5. Analytics             — insights across all your sessions")
            print("  6. Export                — save sessions to a CSV file")
            print("  7. Help                  — how to use the app")
            print("  8. Quit")
            print()
            raw = input("  Choice: ").strip()

            nav = ui.handle_nav(raw)
            if nav == ui.NAV_QUIT or raw == "8":
                break

            if raw == "1":
                result = ui.screen_add_topic()
            elif raw == "2":
                result = ui.screen_log_session()
            elif raw == "3":
                result = ui.menu_my_sessions()
            elif raw == "4":
                result = ui.menu_my_topics()
            elif raw == "5":
                result = ui.screen_analytics()
            elif raw == "6":
                result = ui.screen_export()
            elif raw == "7":
                result = ui.screen_help()
            else:
                continue

            if result == ui.NAV_QUIT:
                break

    ui.clear()
    print("\n  See you next session.\n")


if __name__ == "__main__":
    main()