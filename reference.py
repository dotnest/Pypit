import logging
logging.basicConfig(level=logging.INFO)

from ahk import AHK, Hotkey
from ahk.window import Window

ahk = AHK()

win = ahk.active_window


key_combo = '^c' # Define an AutoHotkey key combonation
script = f'ToolTip, {"".join(["%", "clipboard%"])}' # Define an ahk script
hotkey = Hotkey(ahk, key_combo, script) # Create Hotkey
hotkey.start()  #  Start listening for hotkey

print(win.process)
input()
hotkey.stop()