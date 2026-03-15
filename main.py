# main.py
# Entry point. Runs the main menu loop.
# Calls ui.py for all screens. Never touches db.py or models.py directly.

import ui

def main():
    while True:
        # show home screen
        ui.screen_home()

        # main menu
        print("  MENU")
        ui.line()
        print("  1. Log a session")
        print("  2. Sessions")
        print("  3. Subjects")
        print("  4. Quit")
        print()

        raw = input("  Choice: ").strip()

        # nav commands work from main menu too
        nav = ui.handle_nav(raw)
        if nav == ui.NAV_QUIT:
            break

        if raw == "1":
            result = ui.screen_log_session()
        elif raw == "2":
            result = ui.menu_sessions()
        elif raw == "3":
            result = ui.menu_subjects()
        elif raw == "4":
            break
        else:
            continue

        # NAV_QUIT from any screen exits the app
        if result == ui.NAV_QUIT:
            break
        # NAV_MAIN and NAV_BACK both return to main menu — loop continues

    ui.clear()
    print("\n  See you next session.\n")


if __name__ == "__main__":
    main()
