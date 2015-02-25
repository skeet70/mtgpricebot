import json
import urllib2
import urllib
import os

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
    return set_input.title().replace(' ', '_')


def construct_id(name, set):
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

    data = json.load(urllib2.urlopen(
        'http://www.mtgprice.com/api?apiKey='+os.environ['MTGPRICEAPI']+'&s='+set))
    cards_list = data['cards']
    for card in cards_list:
        cache.put(
            cache="mtgprice",
            key=card['mtgpriceID'],
            value=card['fairPrice'],
            expires_in=86400,
            add=True
        )
    msg = cache.put(
        cache="mtgprice",
        key=set,
        value=True,
        expires_in=86400,
        add=True
    )

    return msg.msg


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
    if card == None:
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
                    card = get_card(construct_name(fuzzy_name, construct_set(input_set)))
                    set_ret = item['set']
                    name_ret = fuzzy_name

        if not card:
            card = get_card(construct_name(fuzzy_name, construct_set(editions[0]['set'])))
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
            set = construct_set(options[1])
            card = get_card(name, set)
            if card.value:
                bot.reply(options[0].title() + ' | MTGPrice.com fair price: ' + card.value + ' | Set: ' + options[1].title())
            else:
                card, fuzzy_name, fuzzy_set = get_deckbrew(options[0], options[1])
                if card.value:
                    bot.reply(
                    fuzzy_name + ' | MTGPrice.com fair price: ' + card.value + ' | Set: ' + fuzzy_set)
                else:
                    bot.reply("No results.")

        elif options[0]:
            card, fuzzy_name, fuzzy_set = get_deckbrew(options[0])
            if card.value:
                bot.reply(
                fuzzy_name + ' | MTGPrice.com fair price: ' + card.value + ' | Set: ' + fuzzy_set)
            else:
                bot.reply("No results.")

        else:
            bot.reply("No results.")

    except Exception as e:
        print(e)
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
