import asyncio
import random
import re
from collections import defaultdict, deque
from contextlib import suppress
from functools import partial
from itertools import product
from typing import Literal, Never

import disnake
from disnake.ext import commands

from arabot.core import Ara, Category, Cog, Context, CustomEmoji
from arabot.utils import AnyMember

CANT_PLAY_VS_SELF = f"{__name__}.cant_play_vs_self"
CANT_PLAY_VS_BOTS = f"{__name__}.cant_play_vs_bots"
NO_WINNER = f"{__name__}.no_winner"

COLUMN_EMOJI = "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣"
CANCEL_EMOJI = "🚪"
BACKGROUND = "⚫"
TOKENS = "🟡", "🔴", "🟠", "🟣", "🟤", "🔵", "⚪"
LAST_COLUMN_INDICATOR = "⬇️"
FILLER = "➖"  # ⬛
BOARD_EMOJI = *COLUMN_EMOJI, CANCEL_EMOJI, BACKGROUND, LAST_COLUMN_INDICATOR, FILLER


class Connect4Engine:
    MOVE_ACCEPTED = 0
    PLAYER1_WINNER = 1
    PLAYER2_WINNER = 2
    INVALID_MOVE = 3
    WRONG_PLAYER = 4
    DRAW = 5

    def __init__(self, player1: int, player2: int):
        self._player1 = player1
        self._player2 = player2
        self._state: list[int] = [0] * 6 * 7

    @property
    def _next_up(self) -> int:
        return self._player1 if self._state.count(0) % 2 == 0 else self._player2

    def _play_move(self, player: int, column: int) -> int:
        # Wrong player
        if self._next_up != player:
            return self.WRONG_PLAYER

        # Invalid column
        if not 1 <= column <= 7:
            return self.INVALID_MOVE

        # Column full
        if self._state[column - 1]:
            return self.INVALID_MOVE

        return self._apply_move(player, column)

    def _apply_move(self, player: int, column: int) -> int:
        next_empty = self._find_next_empty(column)
        self._state[next_empty] = 1 if player == self._player1 else 2
        if self._check_4_in_a_row(next_empty):
            return self.PLAYER1_WINNER if player == self._player1 else self.PLAYER2_WINNER
        return self.MOVE_ACCEPTED if 0 in self._state else self.DRAW

    def _check_4_in_a_row(self, last_added: int) -> bool:
        target_value = self._state[last_added]

        space_right = 6 - last_added % 7
        space_left = last_added % 7
        space_down = 5 - last_added // 7
        space_up = last_added // 7
        directions: dict[int, int] = {
            +1: space_right,
            -1: space_left,
            +7: space_down,
            -7: space_up,
            +6: min(space_down, space_left),
            -6: min(space_up, space_right),
            +8: min(space_down, space_right),
            -8: min(space_up, space_left),
        }

        in_a_row = dict[int, int]()
        for direction, distance in directions.items():
            d = min(distance, 3)
            current = last_added
            while d > 0:
                current += direction
                if self._state[current] != target_value:
                    break
                in_a_row[abs(direction)] = in_a_row.get(abs(direction), 1) + 1
                d -= 1
        return any(x >= 4 for x in in_a_row.values())

    def _find_next_empty(self, column: int) -> int:
        current = column - 1
        while current <= 34 and not self._state[current + 7]:
            current += 7
        return current


class Connect4Game(Connect4Engine):
    def __init__(
        self, player1: disnake.Member, player2: disnake.Member, p1_token: str, p2_token: str
    ):
        self.player1 = player1
        self.player2 = player2
        self.tokens = (BACKGROUND, p1_token, p2_token)
        self.last_column = None
        super().__init__(player1.id, player2.id)

    def play_move(self, player: disnake.Member, column: int) -> int:
        self.last_column = column
        return self._play_move(player.id, column)

    @property
    def next_up(self) -> disnake.Member:
        return self.player1 if self._next_up == self.player1.id else self.player2

    @property
    def state(self) -> list[int]:
        return self._state

    def get_embed(self, custom_footer: bool = False) -> disnake.Embed:
        title = (
            f"Connect 4: {self.player1.display_name} ({self.tokens[1]}) "
            f"VS {self.player2.display_name} ({self.tokens[2]})"
        )
        if c := self.last_column:
            content = FILLER * (c - 1) + LAST_COLUMN_INDICATOR + (FILLER * (7 - c)) + "\n"
        else:
            content = ""

        for line in range(6):
            line_state = self.state[line * 7 : (line + 1) * 7]
            content += "".join(str(self.tokens[x]) for x in line_state) + "\n"

        content += "".join(COLUMN_EMOJI)

        e = disnake.Embed(title=title, description=content, color=0x2ECC71)
        if custom_footer:
            e.set_footer(text=custom_footer)
        else:
            token = self.tokens[1] if self.next_up == self.player1 else self.tokens[2]
            e.set_footer(text=f"Next Up: {self.next_up.display_name} ({token})")

        return e


class Connect4(Cog, category=Category.FUN):
    def __init__(self, ara: Ara):
        self.ara = ara
        self._ = lambda key, msg, scope_depth=1: ara.i18n.getl(
            key, msg.guild.preferred_locale, scope_depth + (scope_depth > 0)
        )
        self.waiting_games = dict[int, tuple[disnake.Message, disnake.Member, str | None]]()
        self.active_games = dict[int, tuple[Connect4Game, disnake.Message]]()

    async def start_invite(self, ctx: Context) -> None:
        await ctx.message.delete()
        message = await ctx.send(ctx._("start_game").format(ctx.author.display_name))
        self.waiting_games[message.id] = (message, ctx.author, None)
        for emoji in TOKENS:
            await message.add_reaction(emoji)
        await message.add_reaction(CANCEL_EMOJI)

    async def p1_token_pick(self, message: disnake.Message, token: str) -> None:
        message, player1, _ = self.waiting_games[message.id]
        self.waiting_games[message.id] = (message, player1, token)
        await message.clear_reaction(token)
        content = message.content.split("\n")[0]
        await message.edit(self._("pick_color", message).format(content, token))

    async def start_game(
        self,
        player1: disnake.Member,
        player2: disnake.Member,
        p1_token: str,
        p2_token: str,
        message: disnake.Message,
    ) -> None:
        await message.clear_reactions()
        notification: disnake.Message = await message.channel.send_ping(
            self._("joined_game", message).format(player1.mention, player2.display_name)
        )
        await message.edit(self._("loading", message))
        for emoji in COLUMN_EMOJI:
            await message.add_reaction(emoji)
        await message.add_reaction(CANCEL_EMOJI)
        game = Connect4Game(player1, player2, p1_token, p2_token)
        self.active_games[message.id] = (game, message)
        await message.edit(None, embed=game.get_embed())
        await notification.delete()

    async def finish_game(self, game: Connect4Game, message: disnake.Message, result: int) -> None:
        await message.clear_reactions()
        if result == game.DRAW:
            winner = None
            footer = "draw"
        elif result == game.PLAYER1_WINNER:
            winner = game.player1.display_name
            footer = "game_won_by"
        elif result == game.PLAYER2_WINNER:
            winner = game.player2.display_name
            footer = "game_won_by"

        await message.edit(
            embed=game.get_embed(custom_footer=self._(footer, message).format(winner))
        )
        del self.active_games[message.id]

    async def cancel_invite(self, message: disnake.Message) -> None:
        await message.delete()
        del self.waiting_games[message.id]

    async def cancel_game(
        self, game: Connect4Game, message: disnake.Message, user: disnake.Member
    ) -> None:
        await message.clear_reactions()
        footer = self._("game_cancelled_by", message)
        await message.edit(embed=game.get_embed(custom_footer=footer.format(user.display_name)))
        del self.active_games[message.id]

    @commands.command(aliases=["c4"], brief="Start a game of Connect 4")
    async def connect4(self, ctx: Context) -> None:
        await self.start_invite(ctx)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: disnake.Reaction, user: disnake.abc.User) -> None:
        if user.id == self.ara.user.id:
            return
        if reaction.message.id in self.waiting_games:
            message, player1, p1_token = self.waiting_games[reaction.message.id]

            if user.id == player1.id:
                emoji = reaction.emoji
                if emoji == CANCEL_EMOJI:
                    await self.cancel_invite(message)
                    return
                if emoji not in BOARD_EMOJI and isinstance(emoji, str) and p1_token is None:
                    await self.p1_token_pick(message, emoji)

            elif p1_token:
                emoji = reaction.emoji
                if emoji not in BOARD_EMOJI and emoji != p1_token and isinstance(emoji, str):
                    player2 = user
                    p2_token = reaction.emoji
                    del self.waiting_games[reaction.message.id]
                    await self.start_game(player1, player2, p1_token, p2_token, message)
                    return

            await message.remove_reaction(reaction.emoji, user)

        elif reaction.message.id in self.active_games:
            game, message = self.active_games[reaction.message.id]
            if game.next_up != user or reaction.emoji not in {*COLUMN_EMOJI, CANCEL_EMOJI}:
                await message.remove_reaction(reaction.emoji, user)
                return

            if reaction.emoji == CANCEL_EMOJI:
                await self.cancel_game(game, message, user)
                return

            result = game.play_move(user, COLUMN_EMOJI.index(reaction.emoji) + 1)
            if result in {game.PLAYER1_WINNER, game.PLAYER2_WINNER, game.DRAW}:
                await self.finish_game(game, message, result)
            elif result == 0:
                await message.edit(embed=game.get_embed())

            await message.remove_reaction(reaction.emoji, user)


class TicTacToeButton(disnake.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=disnake.ButtonStyle.grey, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, inter: disnake.MessageInteraction) -> None:
        view: TicTacToe = self.view
        if view.board[self.y][self.x] is not None:
            return

        notify_wrong_turn = partial(
            inter.response.send_message, "It's not your turn!", ephemeral=True
        )
        if view.current_player is None:
            if view.p1 is None:
                if inter.author == view.p2:
                    await notify_wrong_turn()
                    return
                view.p1 = view.current_player = inter.author
            else:
                if inter.author == view.p1:
                    await notify_wrong_turn()
                    return
                view.p2 = view.current_player = inter.author

        if view.current_player != inter.author:
            if inter.author in {view.p1, view.p2}:
                await notify_wrong_turn()
            else:
                await inter.response.send_message(inter._("not_player"), ephemeral=True)
            return

        if view.current_player is view.p1:
            self.style = disnake.ButtonStyle.red
            self.label = "X"
            view.board[self.y][self.x] = view.p1
            view.current_player = view.p2
            content = inter._("next_turn").format(view.p2.mention if view.p2 else "O")
        else:
            self.style = disnake.ButtonStyle.green
            self.label = "O"
            view.board[self.y][self.x] = view.p2
            view.current_player = view.p1
            content = inter._("next_turn").format(view.p1.mention)
        self.disabled = True

        loser = None
        if winner := view.check_board_winner():
            if winner is True:
                content = inter._("tie")
            else:
                loser = view.p1 if winner is view.p2 else view.p2
                content = inter._("won_against").format(winner.mention, loser.mention)

            for child in view.children:
                child.disabled = True
            view.stop()

        await inter.response.edit_message(
            content, view=view, allowed_mentions=disnake.AllowedMentions.all()
        )

        if loser:
            with suppress(disnake.Forbidden):
                await loser.timeout(duration=60, reason=inter._("loser"))
                await inter.message.reply_ping(
                    inter._("user_muted_1m", False).format(loser.mention)
                )


class TicTacToe(disnake.ui.View):
    def __init__(self, p1: disnake.abc.User, p2: disnake.abc.User):
        super().__init__()
        self.p1 = self.current_player = p1
        self.p2 = p2
        self.board = [
            [None, None, None],
            [None, None, None],
            [None, None, None],
        ]

        for x, y in product(range(3), range(3)):
            self.add_item(TicTacToeButton(x, y))

    def check_board_winner(self) -> disnake.abc.User | bool:
        # Check horizontal
        for across in self.board:
            if across[0] and len(set(across)) == 1:
                return across[0]

        # Check vertical
        for column in range(3):
            if self.board[0][column] is self.board[1][column] is self.board[2][column] is not None:
                return self.board[0][column]

        # Check diagonal
        if (
            self.board[0][2] is self.board[1][1] is self.board[2][0]
            or self.board[0][0] is self.board[1][1] is self.board[2][2]
        ):
            return self.board[1][1]

        # Check tie
        return all(cell for row in self.board for cell in row)


class Games(Cog, category=Category.FUN):
    def __init__(self, ara: Ara):
        self.ara = ara
        self.rr_barrel: dict[int, int] = defaultdict(lambda: [1, random.randint(1, 6)])
        self.rr_last_user: dict[int, int] = {}
        self.rr_last_deaths: dict[int, deque[int]] = defaultdict(partial(deque, maxlen=2))
        self.russian_roulette._buckets = commands.DynamicCooldownMapping(
            self.rr_cooldown, commands.BucketType.guild
        )

    def rr_cooldown(self, msg: disnake.Message) -> commands.Cooldown | None:
        if self.rr_last_user.get(msg.guild.id) != msg.author.id:
            barrel = self.rr_barrel[msg.guild.id]
            if barrel[0] == barrel[1]:
                return commands.Cooldown(1, 60)
        return None

    @commands.command(name="rr", brief="Russian Roulette")
    async def russian_roulette(self, ctx: Context):
        if self.rr_last_user.get(ctx.guild.id) == ctx.author.id:
            await ctx.reply_("pass_gun")
            return

        self.rr_last_user[ctx.guild.id] = ctx.author.id
        barrel = self.rr_barrel[ctx.guild.id]
        if barrel[0] != barrel[1]:
            barrel[0] += 1
            await ctx.reply(f"_\\*{ctx._('click')}*_")
            return

        del self.rr_barrel[ctx.guild.id]
        del self.rr_last_user[ctx.guild.id]

        last_deaths = self.rr_last_deaths[ctx.guild.id]
        if last_deaths.count(ctx.author.id) < last_deaths.maxlen:
            last_deaths.append(ctx.author.id)
            await ctx.reply(f"***{ctx._('gunshot1')}***💥{CustomEmoji.KannaGun}")
            await ctx.send_("cooldown")
            with suppress(disnake.Forbidden):
                await ctx.author.timeout(duration=60, reason=ctx._("russian_roulette"))
            return

        # Same user loses 3 times in a row
        last_deaths.clear()
        await ctx.reply(f"💥***__{ctx._('gunshot2')}__***💥")
        await ctx.send_("cooldown")
        if await ctx.ara.db.get_guild_rr_kick(ctx.guild.id):
            with suppress(disnake.Forbidden):
                await ctx.author.kick(reason=ctx._("russian_roulette"))
                return
        with suppress(disnake.Forbidden):
            await ctx.author.timeout(duration=180, reason=ctx._("russian_roulette"))

    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.command(brief="Guess a number", usage="[max=20]")
    async def guess(self, ctx: Context, *ceiling: str):
        # Initializing
        try:
            ceiling = max(abs(int(ceiling[-1])), 2)
        except (ValueError, IndexError):
            ceiling = 20
        number = random.randint(1, ceiling)
        await ctx.send(ctx._("guess").format(ceiling))

        # Voting phase
        guesses: dict[disnake.Member, int] = {}

        def is_valid_guess(vote: disnake.Message) -> bool:
            if vote.channel == ctx.channel and vote.author not in guesses:
                with suppress(ValueError):
                    return (
                        int(vote.content) not in guesses.values()
                        and 1 <= int(vote.content) <= ceiling
                    )
            return False

        async def voting() -> Literal[True]:
            while True:
                vote: disnake.Message = await ctx.ara.wait_for("message", check=is_valid_guess)
                await vote.blue_tick()
                guesses[vote.author] = int(vote.content)
                if guesses[vote.author] == number:
                    return True

        try:
            exact_guess: disnake.Message = await asyncio.wait_for(voting(), timeout=20)
        except TimeoutError:
            exact_guess = False

        # Winner phase
        if not exact_guess and len(guesses) < 2:
            ctx.reset_cooldown()
            await ctx.send_(NO_WINNER, False)
            return
        winner = min(guesses, key=lambda m: abs(guesses[m] - number))
        message = ctx._("exact_guess" if exact_guess else "close_guess").format(
            winner.mention, number
        )
        try:
            await winner.timeout(duration=60, reason=ctx._("guessed"))
        except disnake.Forbidden:
            pass
        else:
            message += f"\n{ctx._('enjoy_1m_mute')} {CustomEmoji.TeriCelebrate}"
        await ctx.send(message)

    @commands.cooldown(1, 120, commands.BucketType.guild)
    @commands.command(
        aliases=["impostor", "impasta"],
        brief="Eject imposter from voice chat",
        extras={"note": "You have to be in voice chat with other people to use this command"},
    )
    async def imposter(self, ctx: Context):
        if not (vc := getattr(ctx.author.voice, "channel", None)):
            ctx.reset_cooldown()
            await ctx.send_("no_voice_channel")
            return
        if [m.bot for m in vc.members].count(False) < 3:
            ctx.reset_cooldown()
            await ctx.send_("too_few_members")
            return
        if not ctx.author.voice.channel.permissions_for(ctx.me).move_members:
            ctx.reset_cooldown()
            await ctx.send(ctx._("generic.no_perms_to", False).format("move members"))
            return

        # Initializing
        await ctx.send(CustomEmoji.KonoDioDa)
        await ctx.send_("start_voting")

        # Voting phase
        voted: list[disnake.Member] = []
        votes: dict[disnake.Member, int] = defaultdict(int)

        def is_valid_vote(vote: disnake.Message) -> bool:
            return bool(
                vote.author not in voted
                and vote.mentions
                and re.fullmatch(r"<@!?\d{15,21}>", vote.content)
                and vote.channel == ctx.channel
                and vote.author in vc.members
                and vote.mentions[0] in vc.members
                and not vote.mentions[0].bot
            )

        async def voting() -> Never:
            while True:
                vote: disnake.Message = await ctx.ara.wait_for("message", check=is_valid_vote)
                await vote.delete()
                mentioned = vote.mentions[0]
                # Punish whoever voted for a streamer
                if mentioned.voice.self_stream:
                    mentioned = vote.author
                votes[mentioned] += 1
                voted.append(vote.author)

        with suppress(TimeoutError):
            await asyncio.wait_for(voting(), timeout=20)

        # Ejection phase
        if (
            len(voted) < 2
            or not (imposter := max(votes, key=lambda m: votes[m]))
            or imposter not in vc.members
            # Check if only one person has the highest amount of votes
            or list(votes.values()).count(votes[imposter]) != 1
        ):
            await ctx.send_("no_eject")
            return
        await imposter.move_to(None, reason=ctx._("Imposter"))
        await ctx.send_ping(ctx._("ejected").format(imposter.mention))

    @commands.command(brief="Start a game of Tic-Tac-Toe", usage="[opponent]")
    async def ttt(self, ctx: Context, *, opponent: AnyMember = False):
        if opponent is None:
            ctx.reset_cooldown()
            await ctx.reply_("user_not_found", False)
            return
        if ctx.author == opponent:
            ctx.reset_cooldown()
            await ctx.reply_(CANT_PLAY_VS_SELF, False)
            return
        if opponent and opponent.bot:
            ctx.reset_cooldown()
            await ctx.reply_(CANT_PLAY_VS_BOTS, False)
            return
        players = [ctx.author, opponent or None]
        random.shuffle(players)
        first = players[0]
        await ctx.send_ping(
            ctx._("goes_first").format(getattr(first, "mention", "X")), view=TicTacToe(*players)
        )


def setup(ara: Ara):
    ara.add_cog(Connect4(ara))
    ara.add_cog(Games(ara))
