import logging
from collections import defaultdict
from enum import StrEnum
from pathlib import Path
from time import time
from typing import Literal, NotRequired, TypedDict

from disnake.ext.commands import command
from yarl import URL

from arabot.core import Ara, Category, Cog, Config, Context


class NimInputType(StrEnum):
    INPUT_AUDIO = "input_audio"
    AUDIO_URL = "audio_url"
    VIDEO_URL = "video_url"
    IMAGE_URL = "image_url"
    TEXT = "text"


class NimInputBase[T: NimInputType](TypedDict):
    type: T


class NimInputUrl(TypedDict):
    url: str


class NimInputAudioObject(TypedDict):
    data: str
    format: Literal["wav", "mp3"]


class NimInputAudio(NimInputBase[NimInputType.INPUT_AUDIO]):
    input_audio: NimInputAudioObject


class NimInputAudioUrl(NimInputBase[NimInputType.AUDIO_URL]):
    audio_url: NimInputUrl


class NimInputVideoUrl(NimInputBase[NimInputType.VIDEO_URL]):
    video_url: NimInputUrl
    start_offset: NotRequired[int | None]
    duration: NotRequired[int | None]


class NimInputImageUrl(NimInputBase[NimInputType.IMAGE_URL]):
    image_url: NimInputUrl


class NimInputText(NimInputBase[NimInputType.TEXT]):
    text: str


type NimInput = NimInputAudio | NimInputAudioUrl | NimInputVideoUrl | NimInputImageUrl | NimInputText


class NimPrompt(TypedDict):
    role: Literal["system", "assistant", "user"]
    content: str | list[NimInput]


HELP_TEXT = """Video: **mp4** up to **2 minutes**.
Audio: **wav**, **mp3** files up to **1 hour**, 8 kHz and higher sampling rates.
Image: RGB **jpeg**, **png**.
Intended for **English** input.
When replying to a message, includes the last 3 messages from the reply chain as context."""


class Ai(Cog, category=Category.GENERAL):
    API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

    def __init__(self, ara: Ara):
        self.ara = ara
        self.headers = {
            "Authorization": f"Bearer {Config.nvidia_api_key}",
            "Accept": "application/json",
        }
        self.context = defaultdict[int, list[NimPrompt]](list)

        instructions = Path("resources/llm-instructions.md").read_text(encoding="utf-8")
        self.instructions = NimPrompt(role="system", content=instructions)

    @command(brief="Prompt LLM with text, replies and images", help=HELP_TEXT, usage="<prompt and/or media>")
    async def ai(self, ctx: Context):
        prompt = self.ctx_to_prompt(ctx)
        if not prompt:
            await ctx.send_help(ctx.command)
            return

        history = list(filter(None, map(self.prune_expired_media, self.context[ctx.channel.id][-18:])))
        messages = [self.instructions, *history, prompt]

        payload = {
            "messages": messages,
            "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
            "max_tokens": 5000,
            "reasoning_budget": 4000,
            "stream": False,
        }
        async with (
            ctx.typing(),
            self.ara.session.post(self.API_URL, headers=self.headers, json=payload, timeout=60) as response,
        ):
            data = await response.json()
        if not response.ok:
            logging.error("AI payload: %r\nAI response: %r", payload, data)
            response.raise_for_status()

        logging.debug("AI payload: %r\nAI response: %r", payload, data)

        answer: str = data["choices"][0]["message"]["content"]

        ai_response = NimPrompt(role="assistant", content=answer)
        self.context[ctx.channel.id] = [self.instructions, *history[-17:], prompt, ai_response]

        if len(answer) > (maxlen := 1997):
            answer = ".".join(answer[:maxlen].rsplit(".", maxsplit=2)[:-1]) + "..."

        await ctx.reply(answer, mention_author=True)

    @staticmethod
    def ctx_to_prompt(ctx: Context) -> NimPrompt | None:
        items: list[NimInput] = []

        if prompt := ctx.argument_only.strip():
            item = NimInputText(
                type=NimInputType.TEXT,
                text=f"[{ctx.author.id}|{ctx.author.global_name or ctx.author.name}]:{prompt}",
            )
            items.append(item)

        for att in ctx.message.attachments:
            if att.content_type.startswith("image/"):
                item = NimInputImageUrl(type=NimInputType.IMAGE_URL, image_url=NimInputUrl(url=att.url))
                items.append(item)

        return NimPrompt(role="user", content=items) if items else None

    @staticmethod
    def prune_expired_media(item: NimPrompt) -> NimPrompt | None:
        if isinstance(item["content"], str):
            return item

        for idx, input_item in enumerate(item["content"]):
            match input_item["type"]:
                case NimInputType.AUDIO_URL:
                    url = input_item["audio_url"]["url"]
                case NimInputType.VIDEO_URL:
                    url = input_item["video_url"]["url"]
                case NimInputType.IMAGE_URL:
                    url = input_item["image_url"]["url"]
                case _:
                    continue

            url = URL(url)
            if "ex" not in url.query or int(url.query["ex"], base=16) > time():
                continue

            del item["content"][idx]

        return item if item["content"] else None


def setup(ara: Ara):
    ara.add_cog(Ai(ara))
