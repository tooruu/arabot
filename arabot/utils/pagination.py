import disnake


class EmbedPaginator(disnake.ui.View):
    message: disnake.Message | None = None

    def __init__(
        self,
        embeds: list[disnake.Embed],
        *,
        page: int = 0,
        timeout: float | None = 180.0,
        buttons: str = "pn",
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

        self.embeds = embeds
        self.page = page
        self.author = author
        for p, embed in enumerate(self.embeds, 1):
            embed.set_footer(text=f"Page {p} of {len(self.embeds)}")

        for char, item in {
            "f": self.first_page,
            "p": self.prev_page,
            "n": self.next_page,
            "l": self.last_page,
            "d": self.delete,
        }.items():
            if char not in buttons:
                self.remove_item(item)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if not self.message:
            self.message = interaction.message
        if self.author is None or interaction.author == self.author:
            return True
        await interaction.response.send_message(
            interaction._("interaction_not_allowed"), ephemeral=True
        )
        return False

    async def on_timeout(self):
        if self.message:
            await self.message.edit(view=None)

    @disnake.ui.button(emoji="⏪", style=disnake.ButtonStyle.blurple)
    async def first_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.page = 0
        self.first_page.disabled = True
        self.prev_page.disabled = True
        self.next_page.disabled = False
        self.last_page.disabled = False
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @disnake.ui.button(emoji="◀", style=disnake.ButtonStyle.secondary)
    async def prev_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.page -= 1
        self.next_page.disabled = False
        self.last_page.disabled = False
        if self.page == 0:
            self.first_page.disabled = True
            self.prev_page.disabled = True
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @disnake.ui.button(emoji="▶", style=disnake.ButtonStyle.secondary)
    async def next_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.page += 1
        self.first_page.disabled = False
        self.prev_page.disabled = False
        if self.page == len(self.embeds) - 1:
            self.next_page.disabled = True
            self.last_page.disabled = True
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @disnake.ui.button(emoji="⏩", style=disnake.ButtonStyle.blurple)
    async def last_page(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.page = len(self.embeds) - 1
        self.first_page.disabled = False
        self.prev_page.disabled = False
        self.next_page.disabled = True
        self.last_page.disabled = True
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @disnake.ui.button(emoji="❌", style=disnake.ButtonStyle.red)
    async def delete(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.on_timeout()
