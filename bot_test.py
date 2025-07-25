### This method may vary depending on the messaging platform ###

import requests

TOKEN = "YOUR_TOKEN_HERE"
BASE_URL = f"API_LINK_HERE{TOKEN}/"

def get_me():
    url = BASE_URL + "getMe"
    response = requests.get(url)
    return response.json()


def get_updates():
    url = BASE_URL + "getUpdates"
    response = requests.get(url)
    return response.json()

print(get_updates())


input()