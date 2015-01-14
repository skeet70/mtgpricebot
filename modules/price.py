import willie
import json
import urllib2
import urllib
from bs4 import BeautifulSoup


@willie.module.commands('price')
def price(bot, trigger):
    """
    Grab the price for the given card (and optional set). Information can come
    from any API that outputs JSON.
    """
    try:
        options = trigger.group(2).split(' !')
        options = [x.encode('utf-8') for x in options]
        data = json.load(urllib2.urlopen('https://api.deckbrew.com/mtg/cards?'+urllib.urlencode({'name': options[0]})))
        error = ""
        if len(data) > 0:
            data = data[0]
            name = data['name']
            editions = data['editions']
            set_id = ""
            prices = ""
            if len(options) == 2:
                for item in editions:
                    if item['set_id'].lower() == options[1].lower():
                        set_id = item['set_id']
                        prices = item['price']
                if set_id == "":
                    set_id = editions[0]['set_id']
                    prices = editions[0]['price']
                    error += "No printing: " + options[1].upper()
            else:
                set_id = editions[0]['set_id']
                prices = editions[0]['price']
            med = prices['median']
            med_dollars = '${:,.2f}'.format(float(med)/100)
            if error == "":
                bot.reply(name + ' | Avg. price: ' + med_dollars + ' | Set: ' + set_id)
            else:
                bot.reply(name + ' | Avg. price: ' + med_dollars + ' | Set: ' + set_id + ' | ' + error)
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
