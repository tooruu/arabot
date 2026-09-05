import logging
from collections import defaultdict
from enum import StrEnum
from pathlib import Path
from time import time
from typing import Literal, NotRequired, TypedDict

import disnake
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
        self.context = defaultdict[int, list[tuple[int, NimPrompt]]](list)

        instructions = Path("resources/llm-instructions.md").read_text(encoding="utf-8")
        self.instructions = NimPrompt(role="system", content=instructions)

    @command(brief="Prompt LLM with text, replies and images", help=HELP_TEXT, usage="<prompt and/or media>")
    async def ai(self, ctx: Context):
        ctx.message.content = ctx.argument_only.strip()
        nim_prompt = self.msg_to_prompt(ctx.message)
        if not nim_prompt:
            await ctx.send_help(ctx.command)
            return

        history, reply_chain = await self.get_clean_history(ctx)
        messages = [self.instructions, *history, *(p for _, p in reply_chain), nim_prompt]

        payload = {
            "messages": messages,
            "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
            "max_tokens": 5000,
            "reasoning_budget": 4000,
            "stream": False,
        }
        try:
            async with (
                ctx.typing(),
                self.ara.session.post(self.API_URL, headers=self.headers, json=payload, timeout=60) as response,
            ):
                data = await response.json()
        except TimeoutError:
            await ctx.reply_("response_timeout")
            return

        if response.status == 503:
            await ctx.reply_("service_unavailable")
            return

        if not response.ok:
            logging.error("AI payload: %r\nAI response: %r", payload, data)
            response.raise_for_status()

        logging.debug("AI payload: %r\nAI response: %r", payload, data)

        answer: str = data["choices"][0]["message"]["content"]
        ai_response = NimPrompt(role="assistant", content=answer)

        if len(answer) > (maxlen := 1997):
            answer = ".".join(answer[:maxlen].rsplit(".", maxsplit=2)[:-1]) + "..."

        reply_msg = await ctx.reply(answer, mention_author=True)

        memory = self.context[ctx.channel.id]
        memory.extend(reply_chain)  # TODO: Don't append existing messages
        memory.append((ctx.message.id, nim_prompt))
        memory.append((reply_msg.id, ai_response))

        self.context[ctx.channel.id] = memory[-18:]

    async def get_clean_history(self, ctx: Context) -> tuple[list[NimPrompt], list[tuple[int, NimPrompt]]]:
        raw_history = self.context[ctx.channel.id][-18:]
        history: list[NimPrompt] = []
        history_ids = set[int]()

        for msg_id, prompt in raw_history:
            if pruned := self.prune_expired_media(prompt):
                history.append(pruned)
                history_ids.add(msg_id)

        reply_chain: list[tuple[int, NimPrompt]] = []
        current_msg = ctx.message

        for _ in range(3):
            if not (ref := current_msg.reference) or not (ref_msg_id := ref.message_id) or ref in history_ids:
                break

            try:
                ref_msg = ref.cached_message or await ctx.channel.fetch_message(ref_msg_id)
            except disnake.HTTPException:
                break

            if ref_prompt := self.msg_to_prompt(ref_msg):
                reply_chain.insert(0, (ref_msg_id, ref_prompt))
                history_ids.add(ref_msg_id)

            current_msg = ref_msg

        return history, reply_chain

    def msg_to_prompt(self, msg: disnake.Message) -> NimPrompt | None:
        if msg.author == self.ara.user:
            return NimPrompt(role="assistant", content=msg.content) if msg.content else None

        items: list[NimInput] = []
        if msg.content:
            author_name = msg.author.global_name or msg.author.name
            item = NimInputText(type=NimInputType.TEXT, text=f"[{msg.author.id}|{author_name}]:{msg.content}")
            items.append(item)

        for att in msg.attachments:
            if att.content_type and att.content_type.startswith("image/"):
                item = NimInputImageUrl(type=NimInputType.IMAGE_URL, image_url=NimInputUrl(url=att.url))
                items.append(item)

        return NimPrompt(role="user", content=items) if items else None

    @staticmethod
    def prune_expired_media(item: NimPrompt) -> NimPrompt | None:
        if isinstance(item["content"], str):
            return item

        for idx in range(len(item["content"]) - 1, -1, -1):
            input_item = item["content"][idx]
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
