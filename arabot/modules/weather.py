import re
from datetime import UTC, datetime
from time import time
from typing import NotRequired, TypedDict

import disnake
from disnake.ext.commands import command
from disnake.utils import format_dt

from arabot.core import Ara, Category, Cog, Context

type IntOrFloat = int | float
LAT_LON_REGEX = re.compile(
    r"[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)\s*,\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)",
    re.ASCII,
)
ICON_URL = "https://openweathermap.org/img/wn/{}@2x.png"


class GeoData(TypedDict):
    name: str
    local_names: dict[str, str]
    lat: float
    lon: float
    country: str
    state: NotRequired[str]


class WeatherCondition(TypedDict):
    id: int
    main: str
    description: str
    icon: str


class WeatherData(TypedDict):
    coord: dict[str, IntOrFloat]
    weather: list[WeatherCondition]
    main: dict[str, IntOrFloat]
    visibility: 10000
    wind: dict[str, IntOrFloat]
    clouds: dict[str, int]
    dt: int
    sys: dict[str, int]
    timezone: int
    id: int
    name: str
    cod: int


class WeatherFetchError(Exception):
    pass


class Weather(Cog, category=Category.GENERAL, keys={"OPENWEATHER_KEY"}):
    OPENWEATHER_KEY: str
    API = "https://api.openweathermap.org"

    def __init__(self, ara: Ara):
        self.ara = ara

    async def find_geoloc(self, location: str) -> GeoData | None:
        data = await self.ara.session.fetch_json(
            f"{self.API}/geo/1.0/direct",
            params={"appid": self.OPENWEATHER_KEY, "q": location},
        )
        return data[0] if data else None

    async def fetch_weather(
        self, lat: IntOrFloat, lon: IntOrFloat, units: str = "metric", lang: str = "en"
    ) -> WeatherData:
        data = await self.ara.session.fetch_json(
            f"{self.API}/data/2.5/weather",
            params={
                "appid": self.OPENWEATHER_KEY,
                "lat": lat,
                "lon": lon,
                "units": units,
                "lang": lang,
            },
            raise_for_status=False,
        )
        if data["cod"] != 200:
            raise WeatherFetchError(data["message"])
        return data

    @command(brief="Show current weather in a city or at coordinates")
    async def weather(self, ctx: Context, *, location: str):
        if re.fullmatch(LAT_LON_REGEX, location):
            lat, lon = map(float, location.split(","))
        elif loc := await self.find_geoloc(location):
            lat, lon = loc["lat"], loc["lon"]
        else:
            await ctx.send_("loc_not_found")
            return

        try:
            weather = await self.fetch_weather(lat, lon)
        except WeatherFetchError as e:
            await ctx.send(str(e).capitalize())
            return

        embed = (
            disnake.Embed(
                title=weather["name"],
                url=f"https://www.google.com/maps/place/{lat},{lon}",
                description=", ".join(cond["description"] for cond in weather["weather"]),
                timestamp=datetime.fromtimestamp(weather["dt"], tz=UTC),
            )
            .set_thumbnail(url=ICON_URL.format(weather["weather"][0]["icon"]))
            .add_field(ctx._("temperature"), f"{weather["main"]["temp"]}°C")
            .add_field(ctx._("feels_like"), f"{weather["main"]["feels_like"]}°C")
            .add_field(ctx._("humidity"), f"{weather["main"]["humidity"]}%")
            .add_field(ctx._("cloudiness"), f"{weather["clouds"]["all"]}%")
            .set_footer(
                text=ctx._("powered_by", False).format("OpenWeather"),
                icon_url="https://docs.openweather.co.uk/themes/"
                "openweather_docs/assets/img/icons/logo_60x60.png",
            )
        )
        phase = "sunrise" if time() < weather["sys"]["sunrise"] else "sunset"
        embed.add_field(ctx._(phase), format_dt(weather["sys"][phase], "t"))

        wind = str(weather["wind"]["speed"])
        if gust := weather["wind"].get("gust"):
            wind += f"-{gust}"
        embed.insert_field_at(3, ctx._("wind_speed"), f"{wind} m/s")

        coords = f"{weather["coord"]["lat"]}, {weather["coord"]["lon"]}"
        if not embed.title:
            embed.title = coords
        elif country := weather["sys"].get("country"):
            embed.title += f", {country}"
            embed.set_author(name=coords)
        await ctx.send(embed=embed)


def setup(ara: Ara):
    ara.add_cog(Weather(ara))
