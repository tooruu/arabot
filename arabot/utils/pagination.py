from enum import Flag, auto

import disnake


class ButtonFlag(Flag):
    FIRST = auto()
    PREV = auto()
    NEXT = auto()
    LAST = auto()
    SHARE = auto()
    DELETE = auto()


class EmbedPaginator(disnake.ui.View):
    _DEFAULT_ENABLED_BUTTONS = ButtonFlag.PREV | ButtonFlag.NEXT | ButtonFlag.SHARE
    _DEFAULT_SHARED_BUTTONS = ButtonFlag.FIRST | ButtonFlag.PREV | ButtonFlag.NEXT | ButtonFlag.LAST
    _message: disnake.Message | None = None

    def __init__(
        self,
        embeds: list[disnake.Embed],
        *,
        page: int = 0,
        timeout: float | None = 180.0,
        shared: bool = False,
        buttons: ButtonFlag = _DEFAULT_ENABLED_BUTTONS,
        shared_buttons: ButtonFlag = _DEFAULT_SHARED_BUTTONS,
        author: disnake.abc.User | None = None,
    ):
        if not embeds:
            raise ValueError("Must have at least 1 embed")
        if page > len(embeds) - 1:
            raise IndexError("Embed page out of range")

        super().__init__(timeout=timeout)

        if len(embeds) == 1:
            self.clear_items().stop()
            return

        button_map = {
            ButtonFlag.FIRST: self.first_page,
            ButtonFlag.PREV: self.prev_page,
            ButtonFlag.NEXT: self.next_page,
            ButtonFlag.LAST: self.last_page,
            ButtonFlag.SHARE: self.share,
            ButtonFlag.DELETE: self.delete,
        }

        self._embeds = embeds
        self._page = page
        self._author = author
        self._shared = shared
        self._shared_button_ids = {button_map[b].custom_id for b in shared_buttons}

        for p, embed in enumerate(self._embeds, 1):
            embed.set_footer(text=f"Page {p}/{len(self._embeds)}")

        for button_to_disable in ~buttons:
            self.remove_item(button_map[button_to_disable])

        if ButtonFlag.SHARE in buttons and not shared:
            self._toggle_share()

    def _toggle_share(self) -> None:
        self._shared = not self._shared
        if self._shared:
            self.share.style = disnake.ButtonStyle.red
            self.share.emoji = "🔒"
        else:
            self.share.style = disnake.ButtonStyle.green
            self.share.emoji = "🔓"

    async def _reflect_changes(self, interaction: disnake.MessageInteraction) -> None:
        return await interaction.response.edit_message(embed=self._embeds[self._page], view=self)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if not self._message:
            self._message = interaction.message
        if self._author in {None, interaction.author} or (
            not self._shared and interaction.component.custom_id in self._shared_button_ids
        ):
            return True
        await interaction.response.send_message(
            interaction._("interaction_not_allowed"), ephemeral=True
        )
        return False

    async def on_timeout(self):
        if self._message:
            await self._message.edit(view=None)

    @disnake.ui.button(emoji="⏪", style=disnake.ButtonStyle.blurple, custom_id=f"{__qualname__}.f")
    async def first_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self._page = 0
        await self._reflect_changes(interaction)

    @disnake.ui.button(emoji="◀", style=disnake.ButtonStyle.blurple, custom_id=f"{__qualname__}.p")
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if self._page > 0:
            self._page -= 1
        else:
            self._page = len(self._embeds) - 1
        await self._reflect_changes(interaction)

    @disnake.ui.button(emoji="▶", style=disnake.ButtonStyle.blurple, custom_id=f"{__qualname__}.n")
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if self._page < len(self._embeds) - 1:
            self._page += 1
        else:
            self._page = 0
        await self._reflect_changes(interaction)

    @disnake.ui.button(emoji="⏩", style=disnake.ButtonStyle.blurple, custom_id=f"{__qualname__}.l")
    async def last_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self._page = len(self._embeds) - 1
        await self._reflect_changes(interaction)

    @disnake.ui.button(emoji="🔒", style=disnake.ButtonStyle.red, custom_id=f"{__qualname__}.s")
    async def share(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self._toggle_share()
        await self._reflect_changes(interaction)

    @disnake.ui.button(emoji="❌", style=disnake.ButtonStyle.gray, custom_id=f"{__qualname__}.d")
    async def delete(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.on_timeout()
