import json
import urllib2
import urllib
import os
import traceback

import willie
from iron_cache import *
from bs4 import BeautifulSoup


## THIS IS THE OLD API.DECKBREW METHOD
# @willie.module.commands('price')
# def price(bot, trigger):
#     """
#     Grab the price for the given card (and optional set). Information can come
#     from any API that outputs JSON.
#     """
#     try:
#         options = trigger.group(2).split(' !')
#         options = [x.encode('utf-8') for x in options]
#         data = json.load(urllib2.urlopen('https://api.deckbrew.com/mtg/cards?'+urllib.urlencode({'name': options[0]})))
#         error = ""
#         if len(data) > 0:
#             data = data[0]
#             name = data['name']
#             editions = data['editions']
#             set_id = ""
#             prices = ""
#             if len(options) == 2:
#                 for item in editions:
#                     if item['set_id'].lower() == options[1].lower():
#                         set_id = item['set_id']
#                         prices = item['price']
#                 if set_id == "":
#                     set_id = editions[0]['set_id']
#                     prices = editions[0]['price']
#                     error += "No printing: " + options[1].upper()
#             else:
#                 set_id = editions[0]['set_id']
#                 prices = editions[0]['price']
#             med = prices['median']
#             med_dollars = '${:,.2f}'.format(float(med)/100)
#             if error == "":
#                 bot.reply(name + ' | Avg. price: ' + med_dollars + ' | Set: ' + set_id)
#             else:
#                 bot.reply(name + ' | Avg. price: ' + med_dollars + ' | Set: ' + set_id + ' | ' + error)
#         else:
#             bot.reply("No results.")
#     except Exception as e:
#         print(e)
#         bot.reply("No results (or you broke me).")

def construct_name(name_input):
    """
    Construct a spaceless name for use with MTGPrice's API.
    """
    return name_input.title().replace(' ', '_')


def construct_set(set_input):
    """
    Construct a spaceless set name for use with MTGPrice's API.
    """
    if set_input.title() in set_symbols:
        set_input = set_symbols[set_input.title()]

    return set_input.title().replace(' ', '_')


def construct_id(name_input, set_input):
    """
    Construct the MTGPrice API ID for use with the cache.
    """
    name = construct_name(name_input)
    set = construct_set(set_input)

    return name + set + "falseNM-M"


def load_set(set):
    """
    Loads a set into the cache, only fired if the set_marker isn't already
    there. All cache items expire after a day.
    """
    cache = IronCache()

    html = urllib2.urlopen('http://www.mtgprice.com/api?apiKey='+os.environ['MTGPRICEAPI']+'&s='+set)
    data = None

    data = json.load(html)

    cards_list = data['cards']
    for card in cards_list:
        cache.put(
            cache="mtgprice",
            key=card['mtgpriceID'],
            value=card['fairPrice'],
            options={"expires_in": 86400, "add": True}
        )
    msg = cache.put(
        cache="mtgprice",
        key=set,
        value="True",
        options={"expires_in": 86400, "add": True}
    )

    return True


def set_exists(set):
    """
    Checks if the set has been loaded into the cache. This is our way of knowing
    if a card really exists or if it's just not with us without looping forever.
    """
    cache = IronCache()

    try:
        set_marker = cache.get(cache="mtgprice", key=set)
    except:
        set_marker = None

    if set_marker:
        return True
    else:
        return False


def get_card(name, set):
    """
    Gets a single card of the form card.value and card.key. Trys to get it out
    of the cache, and if that fails it trys to load the set.
    """
    cache = IronCache()
    card = None

    try:
        card = cache.get(cache="mtgprice", key=construct_id(name, set))
    except:
        card = None
    if not card:
        if set_exists(set):
            return None
        else:
            load_set(set)
            card = get_card(name, set)

    return card


def get_deckbrew(input_name, input_set=None):
    """
    To be used when the cache and mtgprice have failed. This should let us do
    some fuzzy name only matches.
    """
    data = json.load(urllib2.urlopen('https://api.deckbrew.com/mtg/cards?'+urllib.urlencode({'name': input_name})))
    card = None
    set_ret = None
    name_ret = None

    if len(data) > 0:
        data = data[0]
        fuzzy_name = data['name']
        editions = data['editions']

        if input_set:
            for item in editions:
                if item['set'].lower() == input_set.lower():
                    card = get_card(construct_name(fuzzy_name), construct_set(input_set))
                    set_ret = item['set']
                    name_ret = fuzzy_name

        if not card:
            card = get_card(construct_name(fuzzy_name), construct_set(editions[0]['set']))
            set_ret = editions[0]['set']
            name_ret = fuzzy_name

    return card, name_ret, set_ret


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
            name = construct_name(options[0])
            set_name = construct_set(options[1])
            card = get_card(name, set_name)
            if card:
                bot.reply(options[0].title() + ' | MTGPrice.com fair price: ' + card.value + ' | Set: ' + options[1].title())
            else:
                card, fuzzy_name, fuzzy_set = get_deckbrew(options[0], options[1])
                if card:
                    bot.reply(
                    fuzzy_name + ' | MTGPrice.com fair price: ' + card.value + ' | Set: ' + fuzzy_set)
                else:
                    bot.reply("No results.")

        elif options[0]:
            card, fuzzy_name, fuzzy_set = get_deckbrew(options[0])
            if card:
                bot.reply(
                fuzzy_name + ' | MTGPrice.com fair price: ' + card.value + ' | Set: ' + fuzzy_set)
            else:
                bot.reply("No results.")

        else:
            bot.reply("No results.")

    except Exception as e:
        traceback.print_exc()
        print(e.args[0])
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
        data = json.load(urllib2.urlopen('https://api.deckbrew.com/mtg/cards?'+urllib.urlencode({'name': option})))
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

set_symbols = {
    "10E": "Core_Set_-_Tenth_Edition",
    "2ED": "Unlimited",
    "3ED": "Revised_Edition",
    "4ED": "Fourth_Edition",
    "5DN": "Fifth_Dawn",
    "5ED": "Fifth_Edition",
    "6ED": "Classic_(Sixth_Edition)",
    "7ED": "Seventh_Edition",
    "8ED": "Core_Set_-_Eighth_Edition",
    "9ED": "Core_Set_-_Ninth_Edition",
    "ALA": "Shards_of_Alara",
    "ALL": "Alliances",
    "APC": "Apocalypse",
    "ARB": "Alara_Reborn",
    "ARC": "Archenemy",
    "ARN": "Arabian_Nights",
    "ATQ": "Antiquities",
    "AVN": "Ajani_vs._Nicol_Bolas",
    "AVR": "Avacyn_Restored",
    "BNG": "Born_of_the_Gods",
    "BOK": "Betrayers_of_Kamigawa",
    "BRB": "Battle_Royale",
    "BTD": "Beatdown",
    "C13": "Commander_2013",
    "C14": "Commander_2014",
    "CHK": "Champions_of_Kamigawa",
    "CHR": "Chronicles",
    "CNS": "Conspiracy",
    "COM": "Commander",
    "CON": "Conflux",
    "CSP": "Coldsnap",
    "DDG": "Knights_vs._Dragons",
    "DDI": "Venser_vs._Koth",
    "DDJ": "Izzet_vs._Golgari",
    "DDK": "Sorin_vs._Tibalt",
    "DDM": "Jace_vs._Vraska",
    "DDN": "Speed_vs._Cunning",
    "DDO": "Elspeth_vs._Kiora",
    "DGM": "Dragon's_Maze",
    "DIS": "Dissension",
    "DKA": "Dark_Ascension",
    "DKM": "Deckmasters",
    "DPA": "Duels_of_the_Planeswalkers",
    "DRB": "From_the_Vault:_Dragons",
    "DRK": "The_Dark",
    "DST": "Darksteel",
    "DVD": "Divine_vs._Demonic",
    "EVE": "Eventide",
    "EVG": "Elves_vs._Goblins",
    "EVT": "Elspeth_vs._Tezzeret",
    "EXO": "Exodus",
    "FEM": "Fallen_Empires",
    "FRF": "Fate_Reforged",
    "FTV": "From_the_Vault:_Twenty",
    "FUT": "Future_Sight",
    "FVR": "From_the_Vault:_Realms",
    "GPT": "Guildpact",
    "GTC": "Gatecrash",
    "GVL": "Garruk_vs._Liliana",
    "H09": "Slivers",
    "H10": "Fire_&_Lightning",
    "HML": "Homelands",
    "HVM": "Heroes_vs._Monsters",
    "ICE": "Ice_Age",
    "INV": "Invasion",
    "ISD": "Innistrad",
    "JOU": "Journey_into_Nyx",
    "JUD": "Judgment",
    "JVC": "Jace_vs._Chandra",
    "KTK": "Khans_of_Tarkir",
    "LEA": "Limited_Edition_Alpha",
    "LEB": "Limited_Edition_Beta",
    "LEG": "Legends",
    "LGN": "Legions",
    "LRW": "Lorwyn",
    "M10": "2010_Core_Set",
    "M11": "2011_Core_Set",
    "M12": "2012_Core_Set",
    "M13": "2013_Core_set",
    "M14": "2014_Core_set",
    "M15": "2015_Core_set",
    "MBS": "Mirrodin_Besieged",
    "MDE": "Modern_Event_Deck_2014",
    "MIR": "Mirage",
    "MM_": "Modern_Masters",
    "MMQ": "Mercadian_Masques",
    "MOR": "Morningtide",
    "MRD": "Mirrodin",
    "NMS": "Nemesis",
    "NPH": "New_Phyrexia",
    "ODY": "Odyssey",
    "ONS": "Onslaught",
    "P12": "Planechase_2012_Edition",
    "PCY": "Prophecy",
    "PD3": "Graveborn",
    "PLC": "Planar_Chaos",
    "PLS": "Planeshift",
    "POR": "Portal",
    "PPR": "Promo_Cards",
    "PVC": "Phyrexia_vs._Coalition",
    "RAV": "Ravnica:_City_of_Guilds",
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
    "UDS": "Urza's_Destiny",
    "UGL": "Unglued",
    "ULG": "Urza's_Legacy",
    "UNH": "Unhinged",
    "USG": "Urza's_Saga",
    "V09": "From_the_Vault:_Exiled",
    "V11": "From_the_Vault:_Legends",
    "V14": "From_the_Vault:_Annihilation",
    "VIS": "Visions",
    "WCS": "World_Championships",
    "WTH": "Weatherlight",
    "WWK": "Worldwake",
    "ZEN": "Zendikar",
}
