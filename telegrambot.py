#!/usr/bin/python3

# Based on https://www.codementor.io/garethdwyer/building-a-telegram-bot-using-python-part-1-goi5fncay

import json
import requests
import urllib
import subprocess


with open('token.telegram', 'r') as myfile:
    TOKEN = myfile.read().replace('\n', '')

URL = "https://api.telegram.org/bot%s/" % (TOKEN)


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    try:
        content = get_url(url)
        js = json.loads(content)
    except:
        js = {u'result': []}
    if 'result' not in js.keys():
        js[u'result'] = []
    return js


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=120"
    if offset:
        url += "&offset=%d" % (offset)
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)


def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text=%s&chat_id=%d" % (text, chat_id)
    get_url(url)


def parse_all(updates):
    for update in updates["result"]:
        try:
            if (update["message"]["text"] == "/ibex"):
                subprocess.call("./stockReport.py '^IBEX'", shell=True)
            elif (update["message"]["text"] == "/dowjones"):
                subprocess.call("./stockReport.py '^DJI'", shell=True)
            elif (update["message"]["text"] == "/nasdaq"):
                subprocess.call("./stockReport.py 'NASDAQ:^IXIC'", shell=True)
            elif (update["message"]["text"] == "/ericsson"):
                subprocess.call("./stockReport.py 'STO:ERIC-B'", shell=True)
            elif (update["message"]["text"] == "/holaluz"):
                subprocess.call("./stockReport.py 'HLZ.MC'", shell=True)
            else:
                text = update["message"]["text"]
                chat = update["message"]["chat"]["id"]
                send_message(text, chat)
        except Exception as e:
            print(e)


def main():
    last_update_id = None
    while (True):
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            parse_all(updates)


if __name__ == '__main__':
    main()
