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
    if message.content[0] != '!':
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
    if category == 'game':
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
            await message.reply("게임을 선택해 주세요", view=GameSelectView(gamelist=gamelist, gamedatalist=gamedatalist))
    elif category == 'brand':
        brandname = []
        brandtable = []
        branddata = [] # 회사 정보 출력할 예정
        resultContent = bsObject.find_all("div", {"id":"result"})[0]
        for data in resultContent.find_all("h3"):
            brandname.append(data.find("a").get_text())
        if len(brandname) > 25:
            await message.reply("검색된 정보가 너무 많습니다. 더 자세히 입력해 주세요.")
            return
        for data in resultContent.find_all("table"):
            brandtable.append(data)
            print(data)
        await message.reply("회사를 선택해 주세요", view=BrandSelectView(brandname=brandname, brandtable=brandtable))
        pass

# 게임 정보 객체를 생성하는 함수
# 게임 정보 화면으로 아예 들어가서 정보를 새로 추출하는거로 수정 예정
def createGameEmbed(gamedata):
    gameurl = "https://erogamescape.dyndns.org/~ap2/ero/toukei_kaiseki/" + gamedata[0].find("a").get("href")
    html = urlopen(gameurl)
    bsObject = BeautifulSoup(html, "html.parser")
    imgObject = bsObject.find("div", {"id":"main_image"})
    basictable = bsObject.find("table", {"id":"basic_information_table"})
    statistictable = bsObject.find("table", {"id":"statistics_information_table"})
    
    titleobject = bsObject.find("div", {"id":"soft-title"}).find_all("span")
    gamename = titleobject[0].get_text()
    try:
        gamename += titleobject[1].get_text()    
    except:
        pass
    
    gameimg = imgObject.find("img").get("src")
    gameurl = imgObject.find("a").get("href")
    
    gamebrand = basictable.find("td").get_text()
    gamerelease = basictable.find_all("td")[1].get_text()
    
    gamescore = statistictable.find("tr", {"id":"median"}).find("td").get_text()
    
    embed = discord.Embed(title=gamename, url=gameurl)
    embed.add_field(name="회사", value=gamebrand, inline=False)
    embed.add_field(name="발매일", value=gamerelease, inline=False)
    embed.add_field(name="점수", value=gamescore, inline=False)
    embed.set_thumbnail(url=gameimg)
    return embed

###################################### 게임 검색 UI ###########################################

class GameSelect(discord.ui.Select):
    def __init__(self, gamelist, gamedatalist):
        gameoption = []
        self.gamedatalist = gamedatalist
        for i, game in enumerate(gamelist):
            gameoption.append(discord.SelectOption(label=f"{i+1}. {game}"))
        super().__init__(placeholder="게임을 선택해 주세요", max_values=1, min_values=1, options=gameoption)
    async def callback(self, interaction: discord.Interaction):
        selectedgame = int(self.values[0][:self.values[0].find('.')])-1
        await interaction.response.send_message(embed=createGameEmbed(self.gamedatalist[selectedgame].find_all("td")))

class GameSelectView(discord.ui.View):
    def __init__(self, gamelist, gamedatalist, timeout=30):
        super().__init__(timeout=timeout)
        self.add_item(GameSelect(gamelist, gamedatalist))

###################################### 회사 검색 UI ###########################################

class BrandSelect(discord.ui.Select):
    def __init__(self, brandname, brandtable):
        brandoption = []
        self.brandtable = brandtable
        for i, brand in enumerate(brandname):
            brandoption.append(discord.SelectOption(label=f"{i+1}. {brand}"))
        super().__init__(placeholder="회사를 선택해 주세요", max_values=1, min_values=1, options=brandoption)
    async def callback(self, interaction: discord.Interaction):
        selectedbrand = int(self.values[0][:self.values[0].find('.')])-1
        
        tableContent = self.brandtable[selectedbrand].find_all("tr")
        if len(tableContent) > 26:
            await interaction.response.send_message("해당 회사의 작품이 25개를 초과하여 리스트를 보여드릴 수 없습니다.")
            return
        if len(tableContent) == 2:
            gamedata = tableContent[1].find_all("td")
            await interaction.response.send_message(embed=createGameEmbed(gamedata))
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
            await interaction.response.send_message("게임을 선택해 주세요", view=GameSelectView(gamelist=gamelist, gamedatalist=gamedatalist))
        

class BrandSelectView(discord.ui.View):
    def __init__(self, brandname, brandtable, timeout=30):
        super().__init__(timeout=timeout)
        self.add_item(BrandSelect(brandname, brandtable))