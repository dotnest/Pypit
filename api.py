import requests
import logging
import config
from items import *

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")

LEAGUE = config.load()["league"]
POENINJA_API_BASE_URL = "https://poe.ninja/api/data/"
POE_LEAGUES_URL = "https://www.pathofexile.com/api/trade/data/leagues"
# headers required to get a response
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
}


def get_current_leagues():
    leagues_response = requests.get(POE_LEAGUES_URL, headers=HEADERS).json()["result"]

    leagues_response = [league["id"] for league in leagues_response]

    return leagues_response


def get_currency_url(currency_type):
    return f"{POENINJA_API_BASE_URL}currencyoverview?league={LEAGUE}&type={currency_type}&language=en"


def get_item_url(item_type):
    return f"{POENINJA_API_BASE_URL}itemoverview?league={LEAGUE}&type={item_type}&language=en"


poeninja_category = {
    currency: "currency",
    fragments: "fragments",
    divination_cards: "divination-cards",
    prophecies: "prophecies",
    oils: "oils",
    incubators: "incubators",
    unique_weapons: "unique-weapons",
    unique_armours: "unique-armours",
    unique_accessories: "unique-accessories",
    unique_flasks: "unique-flasks",
    unique_jewels: "unique-jewels",
    skill_gems: "skill-gems",
    maps: "maps",
    blighted_maps: "blighted-maps",
    unique_maps: "unique-maps",
    delirium_orbs: "delirium-orbs",
    invitations: "invitations",
    scarabs: "scarabs",
    watchstones: "watchstones",
    fossils: "fossils",
    resonators: "resonators",
    helm_enchants: "helmet-enchants",
    beasts: "beasts",
    essences: "essences",
    vials: "vials",
}

chaos_value_item_names = frozenset(
    delirium_orbs.union(
        watchstones,
        oils,
        incubators,
        scarabs,
        fossils,
        resonators,
        essences,
        divination_cards,
        prophecies,
        unique_jewels,
        unique_flasks,
        unique_weapons,
        unique_armours,
        unique_accessories,
        vials,
        beasts,
        skill_gems,
        helm_enchants,
        unique_maps,
        maps,
        blighted_maps,
        invitations,
    )
)


get_value_dict = {
    chaos_value_item_names: "chaosValue",
    currency.union(fragments): "chaosEquivalent",
}


name_to_URL_dict = {
    currency: get_currency_url("Currency"),
    fragments: get_currency_url("Fragment"),
    delirium_orbs: get_item_url("DeliriumOrb"),
    watchstones: get_item_url("Watchstone"),
    oils: get_item_url("Oil"),
    incubators: get_item_url("Incubator"),
    scarabs: get_item_url("Scarab"),
    fossils: get_item_url("Fossil"),
    resonators: get_item_url("Resonator"),
    essences: get_item_url("Essence"),
    divination_cards: get_item_url("DivinationCard"),
    prophecies: get_item_url("Prophecy"),
    unique_jewels: get_item_url("UniqueJewel"),
    unique_flasks: get_item_url("UniqueFlask"),
    unique_weapons: get_item_url("UniqueWeapon"),
    unique_armours: get_item_url("UniqueArmour"),
    unique_accessories: get_item_url("UniqueAccessory"),
    vials: get_item_url("Vial"),
    beasts: get_item_url("Beast"),
    skill_gems: get_item_url("SkillGem"),
    helm_enchants: get_item_url("HelmetEnchant"),
    unique_maps: get_item_url("UniqueMap"),
    maps: get_item_url("Map"),
    invitations: get_item_url("Invitation"),
    blighted_maps: get_item_url("BlightedMap"),
}
