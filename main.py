# i'm new to this and it's a dev (hopefully) branch, have some mercy

from pynput.keyboard import Key, KeyCode, Listener, Controller
import pyperclip
from time import sleep
from ahk import AHK, Hotkey
from ahk.window import Window
import sample_items
import logging
logging.basicConfig(level=logging.INFO)

ahk = AHK()
clipboard = pyperclip.paste()
keyboard = Controller()
script = f'ToolTip, {clipboard}, 500, 500'
hotkey = Hotkey(ahk, "^p", script)
persistent = "#Persistent\n"
sleepscr = "Sleep 1000"

def quit_func():
    """ Function for properly closing ahk hotkey listener and quitting this script """
    print('Executed quit_func')
    hotkey.stop()
    quit()

def display_item_in_tooltip(item):
    # https://www.autohotkey.com/docs/Tutorial.htm#s3
    # TODO: read up on {Raw} tag, might not need to format item text with it
    # TODO: reading ahk documentation first before writing this much MIGHT have been a good idea
    ahk.run_script(f'ToolTip, \n(\n{item}\n)\n{sleepscr}')

def format_raw_item(item):
    """ Cleans up raw clipboard item text for usage in ahk script """
    strings_to_remove = ["\r", "--------\n", "\"", "'"]
    result = item.replace("%", "perc")
    for string in strings_to_remove:
        result = result.replace(string, "")
    result = result.split("\n")  # make it a readable list
    result = "`n".join(result)  # join list elements with ahk's newline
    return result

def clipboard_to_tooltip():
    """ Gets item's text from clipboard, formats it, shows a tooltip with it """
    print('Caught ctrl-c')
    # TODO: try removing just the 'c' key to see if i can make chaining tooltips possible with ctrl pressed down
    pressed_vks.clear()  # clearing pressed keys set to prevent weirdness, "There must be a better way!" (c)
    sleep(0.01)  # i think it prevents what's called a race condition? else old clipboard data gets copied
    win = ahk.active_window.process
    print(win)
    if "PathOfExile" in win:
        clipboard = pyperclip.paste()  # get clipboard text from clipboard
        item = format_raw_item(clipboard)  # formats it
        # raw clipboard to tooltip function, but doesn't require formatting to work
        # ahk.run_script(f'ToolTip, {"".join(["%", "clipboard%"])}{sleepscr}')
        display_item_in_tooltip(item)  # alternative, needs more work cleaning out illegal ahk chars
    print("---end---")

def to_hideout():
    pressed_vks.clear()  # clearing pressed keys set to prevent weirdness, "There must be a better way!" (c)
    win = ahk.active_window.process
    print(win)
    if "PathOfExile" in win:
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        keyboard.type("/hideout")
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        sleep(1)  # lord forgive me for this temporary solution while i'm learning stuff

# Create a mapping of keys to function (use frozenset as sets/lists are not hashable - so they can't be used as keys)
# Note the missing `()` after quit_func and clipboard_to_tooltip as want to pass the function, not the return value of the function
combination_to_function = {
    frozenset([Key.ctrl_l, Key.shift, KeyCode(vk=81)]): quit_func,  # shift + q
    frozenset([Key.ctrl_l, KeyCode(vk=67)]): clipboard_to_tooltip,  # left ctrl + c
    frozenset([KeyCode(vk=116)]): to_hideout,
}

# The currently pressed keys (initially empty)
pressed_vks = set()

def get_vk(key):
    """
    Get the virtual key code from a key.
    These are used so case/shift modifications are ignored.
    """
    return key.vk if hasattr(key, 'vk') else key.value.vk

def is_combination_pressed(combination):
    """ Check if a combination is satisfied using the keys pressed in pressed_vks """
    return all([get_vk(key) in pressed_vks for key in combination])

def on_press(key):
    """ When a key is pressed """
    vk = get_vk(key)  # Get the key's vk
    pressed_vks.add(vk)  # Add it to the set of currently pressed keys

    for combination in combination_to_function:  # Loop through each combination
        if is_combination_pressed(combination):  # Check if all keys in the combination are pressed
            combination_to_function[combination]()  # If so, execute the function

def on_release(key):
    """ When a key is released """
    vk = get_vk(key)  # Get the key's vk
    if vk in pressed_vks:
        pressed_vks.remove(vk)  # Remove it from the set of currently pressed keys
    pass

with Listener(on_press=on_press, on_release=on_release) as listener:
    hotkey.start()
    listener.join()