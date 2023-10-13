import discord
import asyncio
from urllib.request import urlopen
from bs4 import BeautifulSoup # 사이트 정보 가져오는 모듈
from urllib import parse
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

TOKEN = ''

@client.event
async def on_ready():
    print(f"Logged in as {client.user.name} {client.user.id}") 

@client.event
async def on_message(message):
    if message.author.id == client.user.id:
        return
    # 일단 게임명 검색만 구현
    print(message.content)
    searchname = None
    category = None
    if message.content[:3] == '!게임':
        category = 'game'
        searchname = message.content[4:]
    elif message.content[:3] == '!회사':
        category = 'brand'
        searchname = message.content[4:]
    elif message.content[:3] == '!등록':
        pass # 약칭같은거 등록하려고 함
    else:
        return
    
    url = 'https://erogamescape.dyndns.org/~ap2/ero/toukei_kaiseki/kensaku.php?category='+category+'&word_category=name&word='+parse.quote(searchname)+'&mode=normal'
    html = urlopen(url)
    bsObject = BeautifulSoup(html, "html.parser")
    tableContent = bsObject.find_all("div", {"id":"result"})[0].find_all("table")[0].find_all("tr")
    if len(tableContent) > 26:
        await message.reply("검색된 정보가 너무 많습니다. 더 자세히 입력해 주세요.")
        return
    if len(tableContent) == 2:
        gamedata = tableContent[1].find_all("td")
        await message.reply(embed=createGameEmbed(gamedata))
        return
    else:
        gamelist = []
        gamedatalist = []
        for content in tableContent[1:]:
            gamename = content.find("a").get_text()
            if content.find("span"):
                gamename += content.find("span").get_text()
            gamelist.append(gamename)
            gamedatalist.append(content)
        await message.reply("게임 선택", view=GameSelectView(gamelist, gamedatalist))

# 게임 정보 객체를 생성하는 함수
def createGameEmbed(gamedata):
    gameurl = gamedata[0].find_all("a")[1].get("href")
    gameimg = gamedata[0].find("img").get("src")
    gamename = gamedata[0].find("a").get_text()
    if gamedata[0].find("span"):
        gamename += gamedata[0].find("span").get_text()
    embed = discord.Embed(title=gamename, url=gameurl)
    embed.add_field(name="회사", value=gamedata[1].get_text(), inline=False)
    embed.add_field(name="발매일", value=gamedata[2].get_text(), inline=False)
    embed.add_field(name="점수", value=gamedata[3].get_text(), inline=False)
    embed.set_thumbnail(url=gameimg)
    return embed

class GameSelect(discord.ui.Select):
    def __init__(self, gamelist, gamedatalist):
        gameoption = []
        self.gamedatalist = gamedatalist
        for i, game in enumerate(gamelist):
            gameoption.append(discord.SelectOption(label=f"{i+1}. {game}"))
        super().__init__(placeholder="게임을 선택해 주세요", max_values=1, min_values=1, options=gameoption)
    async def callback(self, interaction: discord.Interaction):
        selectedgame = int(self.values[0][:self.values[0].find('.')])
        await interaction.response.send_message(embed=createGameEmbed(self.gamedatalist[selectedgame-1].find_all("td")))

class GameSelectView(discord.ui.View):
    def __init__(self, gamelist, gamedatalist, timeout=30):
        super().__init__(timeout=timeout)
        self.add_item(GameSelect(gamelist, gamedatalist))