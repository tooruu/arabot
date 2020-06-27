from discord.ext.commands import Cog
from discord.ext.tasks import loop
from discord import Embed
from selenium import webdriver
from bs4 import BeautifulSoup

class HAnime(Cog):
	def __init__(self, client):
		self.bot = client
		self.channel = None
		self.latest = None
		self.driver = webdriver.PhantomJS()

	@loop(hours=1)
	async def check(self):
		pass
		#connection = cfscrape.create_scraper().get("https://hanime.tv")
		#if connection.status_code == 200:
		#	hanime = BeautifulSoup(connection.content.decode("utf-8"), "html.parser")
		#	new_release = hanime.find_all(class_="htv-carousel__slider")[1][0]
		#	title = new_release.find(class_="hv-title").string.strip()
		#	if title == self.latest:
		#		return
		#	self.latest = title
		#	link = new_release.a["href"]
		#	cover = new_release.find("img")["src"]
		#	await self.channel.send(
		#		"Ara-ara, new release on HAnime! <:RitaPleasure:676909760158629890>",
		#		embed=Embed().set_author(name=title, url="https://hanime.tv" + link).set_thumbnail(url=cover)
		#	)

	@Cog.listener()
	async def on_ready(self):
		self.channel = self.bot.get_channel(676953593148080148) #lewd: 676893776840753155
		#self.check.start() TODO: Account for lazy loading

def setup(client):
	pass
	client.add_cog(HAnime(client))