import httpx
from selectolax.parser import HTMLParser
import re
import time
import random 


url = "https://www.basketball-reference.com/players/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
}

response = httpx.get(url, headers=headers)
html_text = response.text
#emberek betunkenti  keresese   => listaba rakasa majd
#  ez azert kellet mert az a buzi oldal commentelte az egseszet es most ezzel ki veszuk a commentet s rendes html teszuk 
player_list = []
comment_content = re.search(r"<!--\s*(<div class=\"section_content\" id=\"div_alphabet\">.*?</div>)\s*-->", html_text, re.DOTALL)
if comment_content:
    alphabet_html = comment_content.group(1)
    html = HTMLParser(alphabet_html)

    links = html.css("ul.alphabet li a")
    
    for a in links:
        
        href = a.attributes.get("href")
        player_list.append("https://www.basketball-reference.com" + href)
        print(player_list)
print("ELSO LEPES ✅️✅️✅️✅️")





all_players_name = []

#innen indul a masodik lepes a webscraping 
class masodik_lepes:
    def __init__(self):
        self.__header = headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}
        for i, elem in enumerate(player_list):
            
            self.__url = elem
            self.__response = httpx.get(self.__url, headers=self.__header)
            self.__html_text = self.__response.text
            
            comment_content = re.search(r"<!--\s*(<tbody>.*?</tbody>)\s*-->", self.__html_text, re.DOTALL)
            if comment_content:
                html = HTMLParser(comment_content.group(1))
            else:
                html = HTMLParser(self.__html_text)

            self.__links = html.css("tr th a")
            for a in self.__links:
                all_players_name.append((a.text(), a.attributes.get("href")))



            for name, href in all_players_name:
                print(f"{name} | {href}")

            time.sleep(random.uniform(1, 3))    # meg adja az url le scrapeli es majd csak utana megy tovabb.  1/ 3 mp kozot hogy ne latszodjak botnak.

masodik_lepes()
