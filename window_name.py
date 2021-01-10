#!/usr/bin/python3
# https://stackoverflow.com/revisions/36419702/7

import sys

# import logging
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
    if sys.platform in ["linux", "linux2"]:
        # edited to my own solution
        # check the link in beginning of file if you can't make it work
        from Xlib import display, X

        display = display.Display()
        root = display.screen().root
        windowID = root.get_full_property(
            display.intern_atom("_NET_ACTIVE_WINDOW"), X.AnyPropertyType
        ).value[0]
        window = display.create_resource_object("window", windowID)
        active_window_name = window.get_wm_class()[0].lower()

    elif sys.platform in ["Windows", "win32", "cygwin"]:
        # http://stackoverflow.com/a/608814/562769
        import win32gui

        window = win32gui.GetForegroundWindow()
        active_window_name = win32gui.GetWindowText(window)
    elif sys.platform in ["Mac", "darwin", "os2", "os2emx"]:
        # http://stackoverflow.com/a/373310/562769
        from AppKit import NSWorkspace

        active_window_name = NSWorkspace.sharedWorkspace().activeApplication()[
            "NSApplicationName"
        ]
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