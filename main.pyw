#!/usr/bin/python3
from pynput.keyboard import Key, KeyCode, Listener, Controller, GlobalHotKeys
import pyperclip
import tkinter as tk
from time import sleep, time
from datetime import datetime, timedelta
import logging
import requests
import name_to_apiurl as ntu
import window_name
from PIL import Image
import pystray

# maximum response age before it's fetched from poeninja again in minutes
RESPONSE_TTL = 30

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")

keyboard = Controller()
requests_cache = dict()

# TODO: tests with mock api, Item.price(sample.headhunter) == 4950c -> True
# TODO: see if different .gitignore files are possible for dev and
# master branches to keep some dev files in dev branch but not in master


class Item:
    def __init__(self, item_info):
        """Parse raw clipboard data."""
        if not item_info.startswith("Rarity: "):
            logging.info("invalid item data")
            self.name = None
            return None

        # split raw string in a list of individual lines
        if "\r\n" in item_info:
            split_on = "\r\n"
        else:
            split_on = "\n"
        item_info = item_info.split(split_on)

        self.item_info = item_info
        self.rarity = item_info[0].split()[1]
        self.name = item_info[1]
        self.notes = []
        self.value = None
        self.value_str = None

        # self.gem_level and self.gem_quality for gems
        if self.rarity == "Gem":
            if item_info[3].startswith("Vaal"):
                self.name = f"Vaal {self.name}"

            self.gem_level = int(item_info[4].split()[1])
            for line in item_info:
                if line.startswith("Quality: "):
                    self.gem_quality = int(line.split("%")[0].split(": +")[1])
                    break
            else:
                self.gem_quality = 0
        else:
            self.gem_level = None
            self.gem_quality = None

        # self.stack_size and self.stack_size_str, Int and String
        if "Stack Size:" in item_info[3]:
            self.stack_size_str = (
                item_info[3].split(": ")[1].replace("\xa0", "").replace(",", "")
            )
            self.stack_size = int(self.stack_size_str.split("/")[0])
        else:
            self.stack_size_str = ""
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

        # self.enchant for helm enchants
        if self.links and self.links <= 4:
            for line in item_info:
                if line.endswith(" (enchant)"):
                    self.enchant = line[: -len(" (enchant)")]
                    self.name = self.enchant
                    break
            else:
                self.enchant = None

        # self.map_tier for maps
        if item_info[1].endswith(" Map"):
            # special case for superior (quality) unid maps like shaper guardians
            if item_info[1].startswith("Superior "):
                self.name = item_info[1][9:]
            self.map_tier = int(item_info[3].split(": ")[1])
        elif item_info[2].endswith(" Map"):
            # since base map name is offset by random rare map name
            if self.name not in ntu.unique_maps:
                self.name = item_info[2]
            self.map_tier = int(item_info[4].split(": ")[1])
        else:
            self.map_tier = None

        # TODO?: tie in pricecheck to Item.price_one/stack

    def __repr__(self):
        if self.notes:
            ending = "\n".join(self.notes)
            ending = f"{ending}\n---------"
        else:
            ending = "---------"

        return "\n".join(
            [
                self.name,
                f"stack_size={self.stack_size}, corrupted={self.corrupted}",
                f"links=({self.links}, {self.links_str})",
                ending,
            ]
        )


def poe_in_focus():
    """Check if Path of Exile window is in focus."""
    win = window_name.get_active_window()

    if "pathofexile" in win or "Path of Exile" in win:
        return True
    else:
        logging.info(f"{datetime.now()} PoE window isn't in focus")
        return False


def to_hideout():
    """Press enter, input '/hideout', press enter."""
    if poe_in_focus():
        logging.info("Returning to hideout...")
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        # TODO: find a way to make this independent of keyboard layout
        keyboard.type("/hideout")
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        sleep(1)  # lord forgive me for this temporary solution while i'm learning stuff


def request_json(url):
    """Return json for url not older than RESPONSE_TTL minutes."""
    if url not in requests_cache:
        logging.info("adding new entry in dict")
        requests_cache[url] = {
            "time_fetched": datetime.now(),
            "response": requests.get(url).json(),
        }
        return requests_cache[url]["response"]

    response_age = datetime.now() - requests_cache[url]["time_fetched"]
    if response_age > timedelta(minutes=RESPONSE_TTL):
        logging.info("updating entry in dict")
        requests_cache[url] = {
            "time_fetched": datetime.now(),
            "response": requests.get(url).json(),
        }
        return requests_cache[url]["response"]

    logging.info("returning fresh enough response from dict")
    return requests_cache[url]["response"]


def get_url_for_item(item):
    """Return an appropriate api url to call for an item or None if there is not one."""
    for key, value in ntu.name_to_URL_dict.items():
        if item.name in key:
            return value
    else:
        return None


def get_item_value(item, item_json):
    """Return total item value from item_json or None on failure."""
    for items in ntu.get_value_dict:
        if item.name in items:
            json_query = ntu.get_value_dict[items]
            break
    else:
        logging.info("no such item found")
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


def get_ninja_gem_info(item):
    """Return gem's level and quality for poeninja's api."""

    # getting poeninja's appropriate level
    if item.name.startswith("Awakened"):
        if item.gem_level < 5:
            poeninja_level = 1
        elif item.gem_level < 6:
            poeninja_level = 5
        elif item.gem_level >= 6:
            poeninja_level = 6
    else:
        if item.gem_level < 20:
            poeninja_level = 1
        elif item.gem_level < 21:
            poeninja_level = 20
        elif item.gem_level >= 21:
            poeninja_level = 21

    # getting poeninja's appropriate quality
    if item.gem_quality < 20:
        poeninja_quality = 0
    elif item.gem_quality < 23:
        poeninja_quality = 20
    elif item.gem_quality >= 23:
        poeninja_quality = 23

    return (poeninja_level, poeninja_quality)


def press_ctrl_c():
    """Press ctrl-c and add a delay for game to copy item info in clipboard buffer."""
    keyboard.press(Key.ctrl_l)
    keyboard.press(KeyCode(vk=67))
    keyboard.release(Key.ctrl_l)
    keyboard.release(KeyCode(vk=67))
    sleep(0.03)


def pricecheck(item):
    """Return poeninja price for item or None on fail."""
    item_value = None
    pricecheck_time = time()  # tracking pricecheck performance

    # edge case for Chaos Orb
    if item.name == "Chaos Orb":
        r = request_json(ntu.name_to_URL_dict[ntu.currency])
        for line in r["lines"]:
            if line["currencyTypeName"] == "Exalted Orb":
                item_value = line["pay"]["value"]
                logging.info(
                    f"{item.stack_size} {format(item.stack_size * item_value, '.2f')}ex\n"
                )
                return item_value * item.stack_size
        else:
            return None

    # getting appropriate poe.ninja "page" api response
    url = get_url_for_item(item)
    if url is None:
        logging.info("unsupported item")
        return None
    category_json = request_json(url)

    if item.name in ntu.currency or item.name in ntu.fragments:
        name_key = "currencyTypeName"
    else:
        name_key = "name"

    # finding and displaying item value from api response
    for item_json in category_json["lines"]:
        if item.name == item_json[name_key]:
            # special check for items that can be 5l / 6l
            if item.links:
                if item.links < 5:
                    poeninja_links = 0
                else:
                    poeninja_links = item.links
                if item_json["links"] != poeninja_links:
                    item.notes.append(
                        f"{item_json['links']}l - {item_json['chaosValue']}c"
                    )
                    continue

            # special check for gems for level, quality and corruption
            if item.rarity == "Gem":
                ninja_level, ninja_quality = get_ninja_gem_info(item)

                if item_json["corrupted"]:
                    corrupted_str = "\ncorrupted"
                else:
                    corrupted_str = "\n"

                if (
                    ninja_level != item_json["gemLevel"]
                    or ninja_quality != item_json["gemQuality"]
                    or item_json["corrupted"] != item.corrupted
                ):
                    item.notes.append(
                        f"{item_json['gemLevel']}/{item_json['gemQuality']} - {item_json['chaosValue']}c{corrupted_str}"
                    )
                    continue

            # special check for unique maps for map tier
            if item.map_tier:
                if item_json["mapTier"] != item.map_tier:
                    item.notes.append(
                        f"t{item_json['mapTier']} - {item_json['chaosValue']}c"
                    )
                    continue

            logging.info(f"Hit {item.name}")
            item_value = get_item_value(item, item_json)
            if item_value is None:
                logging.info("couldn't find item value")
                return None
            logging.info(f'{item.stack_size} {format(item_value, ".2f")}c')
            break

    logging.info(
        f"Prichecheck finished in {format(time() - pricecheck_time, '.3f')}sec"
    )
    return item_value


def item_info_popup():
    """Show a window with item info."""
    start_time = time()  # for checking total performance
    if not poe_in_focus():
        logging.info("PoE window isn't in focus, returning...\n")
        return -1

    # getting raw item info from the game
    press_ctrl_c()
    item_info = pyperclip.paste()
    item = Item(item_info)
    item.value = pricecheck(item)

    # setting string representation of item.value
    if item.value:
        if item.name == "Chaos Orb":
            item.value_str = f'{format(item.value, ".2f")}ex'
        else:
            item.value_str = f'{format(item.value, ".2f")}c'
    else:
        item.value_str = "no price info"
    logging.debug(item)

    notes = "\n".join(item.notes)
    item_info = f"{item.name}\n{item.stack_size_str}\n{item.value_str}"

    # creating popup window
    window = tk.Tk()
    window.title("Pypit")
    window.after(1, lambda: window.focus_force())  # focus on create
    window.bind("<FocusOut>", lambda e: window.destroy())  # destroy on lose focus
    window.bind("<Escape>", lambda e: window.destroy())  # destroy on Escape
    window.bind("<Control_L>", lambda e: window.destroy())  # destroy on lCtrl

    item_frame = tk.Frame(window, bg="#1e1e1e")
    item_frame.grid()

    # main label with item_info text
    item_label = tk.Label(
        item_frame,
        text=item_info,
        bd=40,
        bg="#1e1e1e",
        fg="#a4b5b0",
        font=("Helvetica", 14),
    )
    item_label.grid()

    # secondary label if there are additional item notes
    if item.notes:
        notes_label = tk.Label(
            item_frame,
            text=notes,
            bd=40,
            bg="#1e1e1e",
            fg="#a4b5b0",
            font=("Helvetica", 12),
        )
        notes_label.grid()

    logging.info(f'Took {format(time() - start_time, ".3f")}sec\n')

    # opening popup window
    window.mainloop()


###################
# pystray functions
###################


def exit_action(icon):
    """Exit the script properly."""
    logging.info("Executed quit_func")
    listener.stop()
    icon.visible = False
    icon.stop()


def setup(icon):
    icon.visible = True

    logging.info("Listening for hotkeys...")
    listener.join()


def init_icon():
    icon = pystray.Icon("pypit")
    icon.menu = pystray.Menu(
        pystray.MenuItem("Exit", lambda: exit_action(icon)),
    )
    icon.icon = Image.open("icon.ico")
    icon.title = "Pypit"

    icon.run(setup)


# TODO: Ctrl-f searches for mouseover item
# TODO: F4 to leave party
# TODO: ctrl-mwheel to scroll through tabs (arrow keys)


hotkey_dict = {"<ctrl>+d": item_info_popup, "<f5>": to_hideout}

if __name__ == "__main__":
    with GlobalHotKeys(hotkey_dict) as listener:
        init_icon()
