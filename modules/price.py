import willie
import json
import urllib2
import urllib
from bs4 import BeautifulSoup


@willie.module.commands('price')
def price(bot, trigger):
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
    try:
        option = trigger.group(2)
        option = option.encode('utf-8')
        data = urllib2.urlopen('http://www.yawgatog.com/resources/magic-rules/')
        soup = BeautifulSoup(data)
        definitions = soup.find('a', id=option).parent.stripped_strings
        if len(definitions) < 10:
            for string in definitions.stripped_strings:
                bot.reply(string)
        elif len(definitions) == 0:
            bot.reply("No results.")
        else:
            bot.reply("Too many results, or I'm broken.")

    except Exception as e:
        print(e)
        bot.reply("No results (or you broke me).")
