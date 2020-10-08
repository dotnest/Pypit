# https://stackoverflow.com/revisions/36419702/7
#!/usr/bin/env python

"""Find the currently active window."""

import logging
import sys

# logging.basicConfig(
#     format="%(asctime)s %(levelname)s %(message)s",
#     level=logging.DEBUG,
#     stream=sys.stdout,
# )


def get_active_window():
    """
    Get the currently active window.

    Returns
    -------
    string :
        Name of the currently active window.
    """

    active_window_name = None
    if sys.platform in ["Windows", "win32", "cygwin"]:
        # http://stackoverflow.com/a/608814/562769
        import win32gui

        window = win32gui.GetForegroundWindow()
        active_window_name = win32gui.GetWindowText(window)
    else:
        print(
            "sys.platform={platform} is unknown. Please report.".format(
                platform=sys.platform
            )
        )
        print(sys.version)
    return active_window_name


if __name__ == "__main__":
    print(f"Active window: {str(get_active_window())}")