import httpx
from selectolax.parser import HTMLParser
import time
import random

url = "https://www.basketball-reference.com/players/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
}

# --- 1️⃣ Betűoldalak lekérése ---
response = httpx.get(url, headers=headers)
html = HTMLParser(response.text)

player_list = []
links = html.css("ul.alphabet li a")
for a in links:
    href = a.attributes.get("href")
    player_list.append("https://www.basketball-reference.com" + href)

print(f"Összes betűoldal: {len(player_list)} ✅")

# --- 2️⃣ Osztály a játékosok lekérésére ---
main_list = []

class masodik_lepes:
    def __init__(self):
        self.__header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}
        for elem in player_list:
            self.__url = elem
            self.__response = httpx.get(self.__url, headers=self.__header)
            self.__html_text = self.__response.text
            html = HTMLParser(self.__html_text)
            
            self.__links = html.css("tr th a")
            for a in self.__links:
                href = a.attributes.get("href")
                full_link = "https://www.basketball-reference.com" + href
                main_list.append(full_link)
                print(full_link)
                time.sleep(random.uniform(1, 2))
    
    def vissza_terites(self):
        return main_list

# --- 3️⃣ Futtatás ---
obj = masodik_lepes()
lista = obj.vissza_terites()

print(f"Összes játékos URL: {len(lista)} ✅")