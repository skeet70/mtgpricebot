import json
import urllib2
import urllib
import os
import traceback

import willie
from iron_cache import *
from bs4 import BeautifulSoup
import titlecase
import requests

set_symbols = {
    "10E": "10th_Edition",
    "15A": "15th Anniversary",
    "2ED": "Unlimited",
    "3ED": "Revised",
    "4ED": "4th_Edition",
    "5DN": "Fifth_Dawn",
    "5ED": "5th_Edition",
    "6ED": "6th_Edition",
    "7ED": "7th_Edition",
    "8ED": "8th_Edition",
    "9ED": "9th_Edition",
    "ALA": "Shards_of_Alara",
    "ALL": "Alliances",
    "APC": "Apocalypse",
    "ARB": "Alara_Reborn",
    "ARC": "Archenemy",
    "ARN": "Arabian_Nights",
    "ATH": "Anthologies",
    "ATQ": "Antiquities",
    "AQ": "Antiquities",
    "AVN": "Duel_Decks_Ajani_vs_Nicol_Bolas",
    "AVR": "Avacyn_Restored",
    "BNG": "Born_of_the_Gods",
    "BOK": "Betrayers_of_Kamigawa",
    "BRB": "Battle_Royale_Box_Set",
    "BTD": "Beatdown_Box_Set",
    "CM1": "Commanders_Arsenal",
    "C13": "Commander_2013",
    "C14": "Commander_2014",
    "CHK": "Champions_of_Kamigawa",
    "CHR": "Chronicles",
    "CNS": "Conspiracy",
    "CMD": "Commander",
    "CON": "Conflux",
    "CSP": "Coldsnap",
    "DDG": "Duel_Decks_Knights_vs_Dragons",
    "DDI": "Duel_Decks_Venser_vs_Koth",
    "DDJ": "Duel_Decks_Izzet_vs_Golgari",
    "DDK": "Duel_Decks_Sorin_vs_Tibalt",
    "DDM": "Duel_Decks_Jace_vs_Vraska",
    "DDN": "Duel_Decks_Speed_vs_Cunning",
    "DDO": "Duel_Decks_Elspeth_vs_Kiora",
    "DGM": "Dragons_Maze",
    "DIS": "Dissension",
    "DKA": "Dark_Ascension",
    "DKM": "Deckmasters",
    "DPA": "Duels_of_the_Planeswalkers",
    "DRB": "From_the_Vault_Dragons",
    "DRK": "The_Dark",
    "DST": "Darksteel",
    "DTK": "Dragons_of_Tarkir",
    "DVD": "Duel_Decks_Divine_vs_Demonic",
    "EVE": "Eventide",
    "EVG": "Duel_Decks_Elves_vs_Goblins",
    "EVT": "Duel_Decks_Elspeth_vs_Tezzeret",
    "EXO": "Exodus",
    "FEM": "Fallen_Empires",
    "FRF": "Fate_Reforged",
    "FTV": "From_the_Vault_Twenty",
    "FUT": "Future_Sight",
    "FVR": "From_the_Vault_Realms",
    "GPT": "Guildpact",
    "GTC": "Gatecrash",
    "GVL": "Duel_Decks_Garruk_vs_Liliana",
    "H09": "Premium_Deck_Series_Slivers",
    "H10": "Premium_Deck_Series_Fire_and_Lightning",
    "HML": "Homelands",
    "HVM": "Duel_Decks_Heroes_vs_Monsters",
    "ICE": "Ice_Age",
    "INV": "Invasion",
    "ISD": "Innistrad",
    "JOU": "Journey_into_Nyx",
    "JUD": "Judgment",
    "JVC": "Duel_Decks_Jace_vs_Chandra",
    "KTK": "Khans_of_Tarkir",
    "LEA": "Alpha",
    "LEB": "Beta",
    "LEG": "Legends",
    "LGN": "Legions",
    "LRW": "Lorwyn",
    "M10": "M10",
    "M11": "M11",
    "M12": "M12",
    "M13": "M13",
    "M14": "M14",
    "M15": "M15",
    "MBS": "Mirrodin_Besieged",
    "MIR": "Mirage",
    "MM2": "Modern_Masters_2015",
    "MMA": "Modern_Masters",
    "MMQ": "Mercadian_Masques",
    "MOR": "Morningtide",
    "MRD": "Mirrodin",
    "NMS": "Nemesis",
    "NPH": "New_Phyrexia",
    "ODY": "Odyssey",
    "ONS": "Onslaught",
    "ORI": "Magic_Origins",
    "P12": "Planechase_2012",
    "PCY": "Prophecy",
    "PD3": "Premium_Deck_Series_Graveborn",
    "PLC": "Planar_Chaos",
    "PLS": "Planeshift",
    "POR": "Portal",
    "PPR": "Promo_Cards",
    "PVC": "Duel_Decks_Phyrexia_vs_Coalition",
    "RAV": "Ravnica",
    "ROE": "Rise_of_the_Eldrazi",
    "RTR": "Return_to_Ravnica",
    "SCG": "Scourge",
    "SHM": "Shadowmoor",
    "SOK": "Saviors_of_Kamigawa",
    "SOM": "Scars_of_Mirrodin",
    "STH": "Stronghold",
    "THS": "Theros",
    "TMP": "Tempest",
    "TOR": "Torment",
    "TSP": "Time_Spiral",
    "UDS": "Urzas_Destiny",
    "UGL": "Unglued",
    "ULG": "Urzas_Legacy",
    "UNH": "Unhinged",
    "USG": "Urzas_Saga",
    "V09": "From_the_Vault_Exiled",
    "V11": "From_the_Vault_Legends",
    "V14": "From_the_Vault_Annihilation",
    "VIS": "Visions",
    "WTH": "Weatherlight",
    "WWK": "Worldwake",
    "ZEN": "Zendikar",
    "S99": "Starter_1999",
    "S00": "Starter_2000"
}


def construct_name(name_input):
    """
    Construct a spaceless name for use with MTGPrice's API.
    """
    print("Constructing a name based on " + name_input)
    return titlecase.titlecase(name_input).replace(' ', '_')


def construct_set(set_input):
    """
    Construct a spaceless set name for use with MTGPrice's API.
    """
    print("Constructing a set based on " + set_input)
    if set_input.upper() in set_symbols:
        print("Found " + set_input + " in set_symbols, passing through.")
        return set_symbols[set_input.upper()]

    return titlecase.titlecase(set_input).replace(' ', '_')


def construct_id(name_input, set_input):
    """
    Construct the MTGPrice API ID for use with the cache.
    """
    name = construct_name(name_input)
    set_name = construct_set(set_input)

    print("Constructing an ID from " + name + " and " + set_name)
    return name + set_name + "falseNM-M"


def load_set(set_name):
    """
    Loads a set into the cache, only fired if the set_marker isn't already
    there. All cache items expire after a day.
    """
    print("Loading set: " + set_name)
    cache = IronCache()

    if set_name.upper() in set_symbols:
        set_name = set_symbols[set_name.upper()]
    print("Calling mtgprice API for set: " + set_name)
    response = requests.get('http://www.mtgprice.com/api?apiKey='+os.environ['MTGPRICEAPI']+'&s=' + set_name)
    data = None

    print("Loading JSON from MTGPrice for: " + set_name)
    data = response.json()

    print("Caching card list for: " + set_name)
    cards_list = data['cards']
    for card in cards_list:
        if "//" not in card['mtgpriceID']:
            cache.put(
                cache="mtgprice",
                key=card['mtgpriceID'],
                value=card['fairPrice'],
                options={"expires_in": 86400, "add": True}
            )
    print("Caching set marker for: " + set_name)
    msg = cache.put(
        cache="mtgprice",
        key=set_name,
        value="True",
        options={"expires_in": 86400, "add": True}
    )

    return True


def set_exists(set_name):
    """
    Checks if the set has been loaded into the cache. This is our way of knowing
    if a card really exists or if it's just not with us without looping forever.
    """
    print("Checking if set " + set_name + " exists in the cache.")
    cache = IronCache()

    try:
        if set_name.upper() in set_symbols:
            set_name = set_symbols[set_name.upper()]
        set_marker = cache.get(cache="mtgprice", key=set_name)
    except:
        set_marker = None

    if set_marker:
        print("Found cached set: " + set_name)
        return True
    else:
        print("Set not found in cache: " + set_name)
        return False


def get_card(name, set_name):
    """
    Gets a single card of the form card.value and card.key. Trys to get it out
    of the cache, and if that fails it trys to load the set.
    """
    cache = IronCache()
    card = None

    try:
        print("Getting card: " + name + " " + set_name)
        card = cache.get(cache="mtgprice", key=construct_id(name, set_name))
    except:
        print("Card not found in cache: " + name + " " + set_name)
        card = None
    if not card:
        if set_exists(construct_set(set_name)):
            print("Card " + name + " " + set_name + " doesn't exist, set is cached.")
            return None
        else:
            print("Set " + set_name + " wasn't found, caching and trying again.")
            load_set(construct_set(set_name))
            card = get_card(name, set_name)

    return card


@willie.module.commands('price')
def price(bot, trigger):
    """
    Grab the price for the given card (and optional set). Information can come
    from any API that outputs JSON.
    """
    try:
        card = None
        options = trigger.group(2).split(' !')
        options = [x.encode('utf-8') for x in options]
        if len(options) > 1:
            print("Name and set passed in, try getting them directly.")
            name = options[0]
            set_name = options[1]
            card = get_card(name, set_name)
            if card:
                print("Found card in cache/MTGPrice, replying.")
                bot.reply(titlecase.titlecase(options[0]) + ' | MTGPrice.com fair price: ' + card.value + ' | Set: ' + construct_set(set_name).replace('_', ' '))
            else:
                print("Card not found in cache/MTGPrice.")
                bot.reply("No results.")

        else:
            print("No searching techniques worked, replying with failure.")
            bot.reply("No results.")

    except Exception as e:
        traceback.print_exc()
        print("Exception while searching: ")
        bot.reply("No results (or you broke me).")


@willie.module.commands('define')
def define(bot, trigger):
    """
    Get the definition for the given keyword or rule. The given keyword needs
    to be an id on yawgatog.com for this to work correctly. Right now it's
    scraping in the future it should hit an API.
    """
    try:
        option = trigger.group(2)
        option = option.encode('utf-8')
        data = urllib2.urlopen('http://www.yawgatog.com/resources/magic-rules/')
        soup = BeautifulSoup(data)
        anchor_tag = soup.find('a', id=option)
        reply = anchor_tag.string
        for sibling in anchor_tag.next_siblings:
            if sibling.string:
                reply = reply + ' ' + sibling.string
        bot.reply(reply)

    except Exception as e:
        print(e)
        bot.reply("No results (or you broke me).")


@willie.module.commands('formats')
def formats(bot, trigger):
    """
    Respond to the user with the format information for a given card.
    """
    try:
        option = trigger.group(2)
        option = option.encode('utf-8')
        data = requests.get('https://api.deckbrew.com/mtg/cards?'+urllib.urlencode({'name': option})).json()
        if len(data) > 0:
            data = data[0]
            name = data['name']
            formats = data['formats']
            output = name + " is "
            for key in formats:
                legality = formats[key]
                if legality == "legal":
                    output = output + "legal in " + key.capitalize() + ", "
                if legality == "restricted":
                    output = output + "legal in " + key.capitalize() + ", "
            out_sections = output.rsplit(",", 1)[0].rsplit(",", 1)
            if len(out_sections) == 1:
                output = out_sections[0] + "."
            else:
                output = out_sections[0] + ", and" + out_sections[1] + "."
            bot.reply(output)
        else:
            bot.reply("No results.")
    except Exception as e:
        print(e)
        bot.reply("No results (or you broke me).")
