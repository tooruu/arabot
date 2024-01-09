import re
from datetime import UTC, datetime
from time import time
from typing import Literal, TypedDict

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
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class Weather(Cog, category=Category.GENERAL, keys={"OPENWEATHER_KEY"}):
    OPENWEATHER_KEY: str
    API = "https://api.openweathermap.org"

    def __init__(self, ara: Ara):
        self.ara = ara

    async def fetch_weather(
        self,
        location: str | tuple[IntOrFloat, IntOrFloat],
        units: Literal["standard", "metric", "imperial"] = "metric",
        lang: str = "en",
    ) -> WeatherData:
        if isinstance(location, str):
            location_data = {"q": location}
        else:
            location_data = dict(zip(("lat", "lon"), location, strict=True))

        data = await self.ara.session.fetch_json(
            f"{self.API}/data/2.5/weather",
            params={"appid": self.OPENWEATHER_KEY, "units": units, "lang": lang} | location_data,
            raise_for_status=False,
        )
        code = int(data["cod"])
        if code != 200:
            raise WeatherFetchError(code, data["message"])
        return data

    @command(brief="Show current weather in a city or at coordinates")
    async def weather(self, ctx: Context, *, location: str):
        if re.fullmatch(LAT_LON_REGEX, location):
            location = map(float, location.split(","))

        try:
            weather = await self.fetch_weather(location)
        except WeatherFetchError as e:
            if e.code == 404:
                await ctx.send_("loc_not_found")
            else:
                await ctx.send(e.message.capitalize())
            return

        lat, lon = weather["coord"]["lat"], weather["coord"]["lon"]
        embed = (
            disnake.Embed(
                title=weather["name"],
                description=", ".join(cond["description"] for cond in weather["weather"]),
                timestamp=datetime.fromtimestamp(weather["dt"], tz=UTC),
            )
            .set_author(name=f"{lat}, {lon}", url=f"https://www.google.com/maps/place/{lat},{lon}")
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
        sunrise, sunset = weather["sys"]["sunrise"], weather["sys"]["sunset"]
        if not sunrise or not sunset:
            embed.add_field("\u200b", "\u200b")  # Align cloudiness field to the grid
        elif sunrise < time() < sunset:
            embed.add_field(ctx._("sunset"), format_dt(sunset, "t"))
        else:
            embed.add_field(ctx._("sunrise"), format_dt(sunrise, "t"))

        wind = str(weather["wind"]["speed"])
        if gust := weather["wind"].get("gust"):
            wind += f"-{gust}"
        embed.insert_field_at(3, ctx._("wind_speed"), f"{wind} m/s")

        if embed.title and (country := weather["sys"].get("country")):
            embed.title += f", {country}"
        await ctx.send(embed=embed)


def setup(ara: Ara):
    ara.add_cog(Weather(ara))
