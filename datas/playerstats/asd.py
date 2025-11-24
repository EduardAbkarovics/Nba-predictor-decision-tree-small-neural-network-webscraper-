import httpx
from selectolax.parser import HTMLParser
import re
import asyncio
import os

BASE_URL = "https://www.basketball-reference.com/players/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
}

# ===============================
# 1️⃣ Betűs ábécé linkek lekérése
# ===============================
async def get_alphabet_links():
    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        resp = await client.get(BASE_URL)
        html_text = resp.text

    comment_content = re.search(
        r"<!--\s*(<div class=\"section_content\" id=\"div_alphabet\">.*?</div>)\s*-->",
        html_text,
        re.DOTALL
    )
    html = HTMLParser(comment_content.group(1)) if comment_content else HTMLParser(html_text)

    links = html.css("ul.alphabet li a")
    alphabet_urls = ["https://www.basketball-reference.com" + a.attributes["href"] for a in links]
    return alphabet_urls

# =========================================
# 2️⃣ Játékosok listázása minden betűhöz
# =========================================
async def get_players_from_letter(url):
    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        resp = await client.get(url)
        html_text = resp.text

    comment_content = re.search(r"<!--\s*(<tbody>.*?</tbody>)\s*-->", html_text, re.DOTALL)
    html = HTMLParser(comment_content.group(1)) if comment_content else HTMLParser(html_text)

    players = []
    for a in html.css("tr th a"):
        name = a.text()
        href = a.attributes.get("href")
        if href:
            players.append((name, "https://www.basketball-reference.com" + href))
    return players

# =========================================
# 3️⃣ Játékos stat táblázatok letöltése
# =========================================
async def download_player_stats(player):
    name, url = player
    safe_name = name.replace("/", "_").replace("\\", "_")
    os.makedirs(f"data/playerstat/{safe_name}", exist_ok=True)

    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        resp = await client.get(url)
        html_text = resp.text

    comment_table = re.search(
        r"<!--\s*(<table[^>]*id=\"per_game_stats\".*?</table>)\s*-->",
        html_text,
        re.DOTALL
    )
    html = HTMLParser(comment_table.group(1)) if comment_table else HTMLParser(html_text)
    table = html.css_first("table#per_game_stats")

    if table:
        table_text = table.text()
        with open(f"data/playerstat/{safe_name}/per_game_stats.txt", "w", encoding="utf-8") as f:
            f.write(table_text)
        print(f"✅ {name} stat mentve")
        return table_text
    return None

# =========================================
# Fő program
# =========================================
async def main():
    # 1️⃣ Ábécé linkek
    alphabet_urls = await get_alphabet_links()
    print(f"Betűs linkek: {len(alphabet_urls)} db")

    # 2️⃣ Minden játékos lekérése
    players = []
    for url in alphabet_urls:
        players += await get_players_from_letter(url)

    # Duplikációk kiszűrése
    seen = set()
    unique_players = []
    for p in players:
        if p not in seen:
            seen.add(p)
            unique_players.append(p)
    print(f"Összes játékos: {len(unique_players)} db")

    # 3️⃣ Statok letöltése (async, max 10 egyidejű letöltés)
    semaphore = asyncio.Semaphore(10)

    async def sem_task(player):
        async with semaphore:
            return await download_player_stats(player)

    await asyncio.gather(*[sem_task(p) for p in unique_players])

# Futtatás
if __name__ == "__main__":
    asyncio.run(main())
