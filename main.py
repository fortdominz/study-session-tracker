# main.py
# Entry point. Runs the main menu loop.
# Calls ui.py for all screens. Never touches db.py or models.py directly.

import ui
import db

def main():
    while True:
        # show home screen
        ui.screen_home()

        # detect first time user — no topics yet
        has_topics = len(db.get_all_subjects()) > 0

        # main menu
        print("  MENU")
        ui.line()

        if not has_topics:
            # first time — guide them to add a topic first
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
            print("  3. My Sessions           — view history, edit, delete")
            print("  4. My Topics             — add, view, archive topics")
            print("  5. Quit")
            print()
            raw = input("  Choice: ").strip()

            nav = ui.handle_nav(raw)
            if nav == ui.NAV_QUIT or raw == "5":
                break

            if raw == "1":
                result = ui.screen_add_topic()
            elif raw == "2":
                result = ui.screen_log_session()
            elif raw == "3":
                result = ui.menu_my_sessions()
            elif raw == "4":
                result = ui.menu_my_topics()
            else:
                continue

            if result == ui.NAV_QUIT:
                break
            # NAV_MAIN and NAV_BACK both return to main menu

    ui.clear()
    print("\n  See you next session.\n")


if __name__ == "__main__":
    main()