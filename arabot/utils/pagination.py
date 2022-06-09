import disnake


class EmbedPaginator(disnake.ui.View):
    def __init__(
        self,
        embeds: list[disnake.Embed],
        *,
        page: int = 0,
        timeout: float | None = 180.0,
        buttons: str = "pn",
    ):
        if not embeds:
            raise ValueError("Must have at least 1 embed")
        if page > len(embeds) - 1:
            raise IndexError("Embed page out of range")

        super().__init__(timeout=timeout)

        if len(embeds) == 1:
            self.clear_items()
            return

        self.embeds = embeds
        self.page = page
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

    @disnake.ui.button(emoji="⏪", style=disnake.ButtonStyle.blurple)
    async def first_page(self, _button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.page = 0
        self.first_page.disabled = True
        self.prev_page.disabled = True
        self.next_page.disabled = False
        self.last_page.disabled = False
        await inter.response.edit_message(embed=self.embeds[self.page], view=self)

    @disnake.ui.button(emoji="◀", style=disnake.ButtonStyle.secondary)
    async def prev_page(self, _button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.page -= 1
        self.next_page.disabled = False
        self.last_page.disabled = False
        if self.page == 0:
            self.first_page.disabled = True
            self.prev_page.disabled = True
        await inter.response.edit_message(embed=self.embeds[self.page], view=self)

    @disnake.ui.button(emoji="▶", style=disnake.ButtonStyle.secondary)
    async def next_page(self, _button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.page += 1
        self.first_page.disabled = False
        self.prev_page.disabled = False
        if self.page == len(self.embeds) - 1:
            self.next_page.disabled = True
            self.last_page.disabled = True
        await inter.response.edit_message(embed=self.embeds[self.page], view=self)

    @disnake.ui.button(emoji="⏩", style=disnake.ButtonStyle.blurple)
    async def last_page(self, _button: disnake.ui.Button, inter: disnake.MessageInteraction):
        self.page = len(self.embeds) - 1
        self.first_page.disabled = False
        self.prev_page.disabled = False
        self.next_page.disabled = True
        self.last_page.disabled = True
        await inter.response.edit_message(embed=self.embeds[self.page], view=self)

    @disnake.ui.button(emoji="❌", style=disnake.ButtonStyle.red)
    async def delete(self, _button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(view=None)
