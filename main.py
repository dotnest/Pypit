from pynput.keyboard import Key, KeyCode, Listener, Controller
import pyperclip
from time import sleep, time
import sample_items
import logging
import requests
from datetime import datetime, timedelta
import name_to_apiurl as ntu
import window_name
import tkinter as tk

# maximum response age before it's fetched from poeninja again
RESPONSE_TTL = 30

logging.basicConfig(level=logging.INFO)

keyboard = Controller()
requests_cache = dict()

# TODO: tests with mock api, Item.price(sample.headhunter) == 4950c -> True
# TODO: see if different .gitignore files are possible for dev and
# master branches to keep some dev files in dev branch but not in master


class Item:
    def __init__(self, item_info):
        """Parse raw clipboard data."""
        item_info = item_info.split("\r\n")
        self.item_info = item_info
        self.rarity = item_info[0].split()[1]
        self.name = item_info[1]

        # self.stack_size and self.stack_size_str, Int and String
        if "Stack Size:" in item_info[3]:
            self.stack_size_str = item_info[3].split(": ")[1].replace("\xa0", "")
            self.stack_size = int(self.stack_size_str.split("/")[0])
        else:
            self.stack_size_str = "1"
            self.stack_size = 1

        # self.corrupted, True or False
        for line in item_info:
            if line == "Corrupted":
                self.corrupted = True
                break
        else:
            self.corrupted = False

        # self.links and self.links_str, both None or Int and String
        for line in item_info:
            if line.startswith("Sockets: "):
                self.links_str = line[9:].strip()
                self.links = max(
                    [len(link) // 2 + 1 for link in self.links_str.split(" ")]
                )
                break
        else:
            self.links_str = None
            self.links = None

        # TODO?: tie in pricecheck to Item.price_one/stack

    def __repr__(self):
        return "\n".join(
            [
                f"{self.name}, corrupted={self.corrupted}",
                f"stack_sizes=({self.stack_size}, {self.stack_size_str})",
                f"links=({self.links}, {self.links_str})",
                "---------",
            ]
        )


def quit_func():
    """Exit the script properly."""
    print("Executed quit_func")
    listener.stop()
    quit()


def poe_in_focus():
    """Check if Path of Exile window is in focus."""
    win = window_name.get_active_window()
    if win != "Path of Exile":
        print("PoE window isn't in focus")
        return False
    return True


def to_hideout():
    """Press enter, input '/hideout', press enter."""
    pressed_vks.clear()  # clearing pressed keys set to prevent weirdness, "There must be a better way!" (c)
    if poe_in_focus():
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        # TODO: find a way to make this independent of keyboard layout
        keyboard.type("/hideout")
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        sleep(1)  # lord forgive me for this temporary solution while i'm learning stuff


def request_json(url):
    """Return json for url not older than RESPONSE_TTL."""
    if url not in requests_cache:
        print("adding new entry in dict")
        requests_cache[url] = {
            "time_fetched": datetime.now(),
            "response": requests.get(url).json(),
        }
        return requests_cache[url]["response"]

    response_age = datetime.now() - requests_cache[url]["time_fetched"]
    if response_age > timedelta(minutes=RESPONSE_TTL):
        print("updating entry in dict")
        requests_cache[url] = {
            "time_fetched": datetime.now(),
            "response": requests.get(url).json(),
        }
        return requests_cache[url]["response"]

    print("returning fresh enough response from dict")
    return requests_cache[url]["response"]


def get_url_for_item(item):
    """Return an appropriate api url to call for an item or None if there is not one."""
    for key, value in ntu.name_to_URL_dict.items():
        if item.name in key:
            return value
    else:
        return None


def get_item_value(item, item_json):
    """Return total item value or None on failure."""
    for key, value in ntu.get_value_dict.items():
        if item.name in value:
            json_query = key
            break
    else:
        print("no such item found")
        return None

    if json_query == "chaosEquivalent":
        if item_json["chaosEquivalent"] > 1:
            # for higher-value items (Mirror, Exalt, Chayula Pure Stone)
            return item.stack_size * item_json["chaosEquivalent"]
        else:
            # for lower-value items (Perandus Coins, Scroll of Wisdom, splinters)
            if item_json["pay"] and item_json["pay"]["value"]:
                return item.stack_size / item_json["pay"]["value"]
            elif item_json["receive"] and item_json["receive"]["value"]:
                return item.stack_size * item_json["receive"]["value"]
    elif json_query == "chaosValue":
        return item.stack_size * item_json["chaosValue"]


def press_ctrl_c():
    """Press ctrl-c and add a delay for game to copy item info in clipboard buffer."""
    keyboard.press(Key.ctrl_l)
    keyboard.press(KeyCode(vk=67))
    keyboard.release(Key.ctrl_l)
    keyboard.release(KeyCode(vk=67))
    sleep(0.03)


def pricecheck(item):
    """Return poeninja price for item"""
    # edge case for Chaos Orb
    pricecheck_time = time()
    if item.name == "Chaos Orb":
        r = request_json(ntu.name_to_URL_dict[ntu.currency])
        for line in r["lines"]:
            if "Exalted Orb" in line["currencyTypeName"]:
                item_value = float(line["receive"]["value"])
                print(
                    f"{item.stack_size} {format(item.stack_size / item_value, '.2f')}ex\n"
                )
                return item_value
        else:
            return None

    # getting appropriate poe.ninja "page" api response
    url = get_url_for_item(item)
    if url is None:
        print("unsupported item")
        return None
    category_json = request_json(url)

    # finding and displaying item value from api response
    for item_json in category_json["lines"]:
        # TODO: optimize item_json.values() to item_json["chaosValue"]/["receive"]["value"]
        if item.name in item_json.values():
            if item.links:
                if item.links < 5:
                    poeninja_links = 0
                else:
                    poeninja_links = item.links
                if item_json["links"] != poeninja_links:
                    print(f"---skipping {item_json['links']}l---")
                    continue
            print("Hit", item.name)
            item_value = get_item_value(item, item_json)
            if item_value is None:
                print("couldn't find item value")
                return None
            print(f'{item.stack_size} {format(item_value, ".2f")}c')
            break

    print(f"Prichecheck finished in {format(time() - pricecheck_time, '.3f')}sec")
    return item_value


def item_info_popup():
    """Show a window with item info."""
    start_time = time()  # for checking pricecheck performance
    pressed_vks.clear()  # clearing pressed keys set to prevent weirdness, "There must be a better way!" (c)
    if not poe_in_focus():
        print("PoE window isn't in focus, returning...\n")
        return -1

    # getting raw item info from the game
    press_ctrl_c()
    item_info = pyperclip.paste()
    item = Item(item_info)
    item.value = pricecheck(item)
    if item.value:
        item.value_str = format(item.value, ".2f")
    else:
        item.value_str = "no price info"
    print(item)

    window = tk.Tk()
    window.after(1, lambda: window.focus_force())  # focus on create
    window.bind("<FocusOut>", lambda e: window.destroy())  # destroy on lose focus
    window.bind("<Escape>", lambda e: window.destroy())  # destroy on Escape

    item_name = tk.Label(text=f"{item.name}\n{item.value_str}c")
    item_name.grid()
    print(f'Took {format(time() - start_time, ".3f")}sec\n')

    window.mainloop()


# Create a mapping of keys to function (use frozenset as sets/lists are not hashable - so they can't be used as keys)
# Note the missing `()` after quit_func and clipboard_to_tooltip as want to pass the function, not the return value of the function
combination_to_function = {
    frozenset([Key.ctrl_l, Key.shift, KeyCode(vk=81)]): quit_func,  # ctrl + shift + q
    frozenset([Key.ctrl_l, KeyCode(vk=68)]): item_info_popup,  # left ctrl + d
    frozenset([KeyCode(vk=116)]): to_hideout,  # F5
    # TODO: Ctrl-f searches for mouseover item
    # TODO: F4 to leave party
}

# The currently pressed keys (initially empty)
pressed_vks = set()


def get_vk(key):
    """
    Get the virtual key code from a key.
    These are used so case/shift modifications are ignored.
    """
    return key.vk if hasattr(key, "vk") else key.value.vk


def is_combination_pressed(combination):
    """Check if a combination is satisfied using the keys pressed in pressed_vks"""
    return all([get_vk(key) in pressed_vks for key in combination])


def on_press(key):
    """When a key is pressed"""
    vk = get_vk(key)  # Get the key's vk
    pressed_vks.add(vk)  # Add it to the set of currently pressed keys

    for combination in combination_to_function:
        if is_combination_pressed(combination):
            combination_to_function[combination]()


def on_release(key):
    """When a key is released"""
    vk = get_vk(key)  # Get the key's vk
    if vk in pressed_vks:
        pressed_vks.remove(vk)  # Remove it from the set of currently pressed keys


with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()