import re
from datetime import UTC, datetime, timedelta, timezone
from io import BytesIO
from time import time
from typing import NotRequired, TypedDict

import disnake
import matplotlib.pyplot as plt
from disnake.ext.commands import command
from disnake.utils import format_dt
from matplotlib.axes import Axes
from matplotlib.dates import ConciseDateFormatter, DateFormatter, DayLocator, HourLocator
from matplotlib.ticker import MaxNLocator

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import I18N

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


class APIResponse(TypedDict):
    cod: int | str
    message: NotRequired[str | int]
    parameters: NotRequired[list[str]]


class WeatherData(TypedDict):
    dt: int
    main: dict[str, IntOrFloat]
    weather: list[WeatherCondition]
    clouds: dict[str, int]
    wind: dict[str, IntOrFloat]
    visibility: int


class Weather(APIResponse, WeatherData):
    coord: dict[str, IntOrFloat]
    base: str
    sys: dict[str, int]
    timezone: int
    id: int
    name: str


class City(TypedDict):
    id: int
    name: str
    coord: dict[str, IntOrFloat]
    country: str
    population: int
    timezone: int
    sunrise: int
    sunset: int


class ForecastDatapoint(WeatherData):
    pop: IntOrFloat
    sys: dict[str, str]
    dt_txt: str


class Forecast(APIResponse):
    cnt: int
    city: City
    list: list[ForecastDatapoint]


class APIFetchError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class WeatherCog(Cog, category=Category.GENERAL, keys={"OPENWEATHER_KEY"}):
    OPENWEATHER_KEY: str
    API = "https://api.openweathermap.org/data/2.5"
    CLOUDINESS = f"{__module__}.cloudiness"
    FEELSLIKE = f"{__module__}.feels_like"
    HUMIDITY = f"{__module__}.humidity"
    SUNRISE = f"{__module__}.sunrise"
    SUNSET = f"{__module__}.sunset"
    TEMPERATURE = f"{__module__}.temperature"
    WIND_SPEED = f"{__module__}.wind_speed"

    def __init__(self, ara: Ara):
        self.ara = ara
        self.fig, ax = plt.subplots(figsize=(6, 2.5), layout="constrained")
        self.ax: Axes = ax

    @command(brief="Show current weather in a city or at coordinates")
    async def weather(self, ctx: Context, *, location: str):
        if re.fullmatch(LAT_LON_REGEX, location):
            location = tuple(map(float, location.split(",")))

        try:
            weather: Weather = await self._openweather_fetch("/weather", location)
            forecast: Forecast = await self._openweather_fetch("/forecast", location)
        except APIFetchError as e:
            if e.code == "404":
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
            .add_field(ctx._(WeatherCog.TEMPERATURE, False), f"{weather["main"]["temp"]}°C")
            .add_field(ctx._(WeatherCog.HUMIDITY, False), f"{weather["main"]["humidity"]}%")
            .add_field(ctx._(WeatherCog.CLOUDINESS, False), f"{weather["clouds"]["all"]}%")
            .set_image(file=self.get_forecast(forecast, ctx._))
            .set_footer(
                text=ctx._("powered_by", False).format("OpenWeather"),
                icon_url="https://docs.openweather.co.uk/themes/"
                "openweather_docs/assets/img/icons/logo_60x60.png",
            )
        )
        wind = str(weather["wind"]["speed"])
        if gust := weather["wind"].get("gust"):
            wind += f"-{gust}"
        embed.insert_field_at(1, ctx._(WeatherCog.WIND_SPEED), f"{wind} m/s")

        sunrise, sunset = weather["sys"]["sunrise"], weather["sys"]["sunset"]
        if not sunrise or not sunset:
            embed.add_field("\u200b", "\u200b")  # Align cloudiness field to the grid
        elif sunrise < time() < sunset:
            embed.add_field(ctx._(WeatherCog.SUNSET), format_dt(sunset, "t"))
        else:
            embed.add_field(ctx._(WeatherCog.SUNRISE), format_dt(sunrise, "t"))

        feels_like = weather["main"]["feels_like"]
        if feels_like != weather["main"]["temp"]:
            embed.insert_field_at(3, ctx._(WeatherCog.FEELSLIKE, False), f"{feels_like}°C")
        else:
            embed.add_field("\u200b", "\u200b")

        if embed.title and (country := weather["sys"].get("country")):
            embed.title += f", {country}"
        await ctx.send(embed=embed)

    def get_forecast(self, forecast: Forecast, _: I18N) -> disnake.File:
        self._graph_forecast(forecast, _)
        file = self.plt_to_file()
        self.fig.axes[1].remove()
        self.ax.clear()
        return file

    def _graph_forecast(self, forecast: Forecast, _: I18N) -> None:
        tz = timezone(timedelta(seconds=forecast["city"]["timezone"]))
        dts = [datetime.fromtimestamp(f["dt"], tz=UTC) for f in forecast["list"]]
        temps = [f["main"]["temp"] for f in forecast["list"]]
        feels = [f["main"]["feels_like"] for f in forecast["list"]]
        humidity = [f["main"]["humidity"] for f in forecast["list"]]
        ax1 = self.ax
        # Configure X axis
        ax1.set(
            xlabel=_("x_label").format(tz),
            xlim=(dts[0], dts[-1]),
            xticks=dts,
            ylabel=f"{_(WeatherCog.TEMPERATURE)}, °C",
        )
        ax1.xaxis.set_major_locator(lct := DayLocator(tz=tz))
        major_tick_formats = ["%d\n%a"] * 6, ["%B %Y"] * 6, ["%b\n%a"] * 6
        ax1.xaxis.set_major_formatter(ConciseDateFormatter(lct, tz, *major_tick_formats))
        ax1.xaxis.set_minor_locator(HourLocator(range(6, 24, 6), tz=tz))
        ax1.xaxis.set_minor_formatter(DateFormatter("%H", tz))
        for label in ax1.get_xminorticklabels():
            label.set(fontsize="x-small", color="grey")
        ax1.grid(axis="x", alpha=0.3)

        # Configure both Y axis
        ax2: Axes = ax1.twinx()
        ax1.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax2.set(ylabel=f"{_(WeatherCog.HUMIDITY)}, %", ylim=(0, 100))

        ax1.plot(dts, temps, "r-.", label=_(WeatherCog.TEMPERATURE, False))
        ax1.plot(dts, feels, color="orange", alpha=0.3, label=_(WeatherCog.FEELSLIKE, False))
        ax2.plot(dts, humidity, color="blue", alpha=0.3, label=_(WeatherCog.HUMIDITY, False))

        self.fig.legend(bbox_to_anchor=(1, 1), bbox_transform=ax1.transAxes, prop={"size": "small"})

    async def _openweather_fetch[T: APIResponse](
        self,
        endpoint: str,
        location: str | tuple[IntOrFloat, IntOrFloat],
        **kwargs: str | IntOrFloat,
    ) -> T:
        if isinstance(location, str):
            location_data = {"q": location}
        else:
            location_data = dict(zip(("lat", "lon"), location, strict=True))

        data: T = await self.ara.session.fetch_json(
            self.API + endpoint,
            params={"appid": self.OPENWEATHER_KEY, "units": "metric", **location_data, **kwargs},
            raise_for_status=False,
        )
        code = str(data["cod"])
        if code != "200":
            raise APIFetchError(code, str(data["message"]))
        return data

    def plt_to_file(self) -> disnake.File:
        buf = BytesIO()
        self.fig.savefig(buf)
        buf.seek(0)
        return disnake.File(buf, "forecast.png")

    def cog_unload(self):
        plt.close(self.fig)


def setup(ara: Ara):
    ara.add_cog(WeatherCog(ara))
