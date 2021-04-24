from random import randint
from asyncio import wait_for, TimeoutError, sleep
from discord.ext.commands import command, Cog, check, BucketType, cooldown


class Guess(Cog, name="Commands"):
    def __init__(self, client):
        self.bot = client

    @cooldown(1, 120, BucketType.guild)
    @command(hidden=True)
    @check(lambda ctx: ctx.guild.id == 676889696302792774)
    async def guess(self, ctx, MAX: int = 20):
        # Initializing
        MAX = abs(MAX)
        TIMEOUT = 20
        MUTED_ROLE = ctx.guild.get_role(751868258130329732)
        NUMBER = randint(1, MAX)
        await ctx.send(f"🎲 Guess a number between 1-{MAX}")
        # Voting phase
        guesses = {}

        def check(vote):
            if vote.channel == ctx.channel and vote.author not in guesses:
                try:
                    return int(vote.content) not in guesses.values() and 1 <= int(vote.content) <= MAX
                except ValueError:
                    pass

        async def ensure():
            while True:
                vote = await self.bot.wait_for("message", check=check)
                await vote.add_reaction("✅")
                guesses[vote.author] = int(vote.content)
                if int(vote.content) == NUMBER:
                    return True

        try:
            exact_guess = await wait_for(ensure(), timeout=TIMEOUT)
        except TimeoutError:
            exact_guess = False
        # Ejection phase
        if exact_guess or len(guesses) > 1:
            winner = min(guesses, key=lambda m: abs(guesses[m] - NUMBER))
            await ctx.send(
                winner.mention + f" {'guessed' if guesses[winner] == NUMBER else 'was the closest to'} "
                f"number {NUMBER}\nEnjoy your 1 minute mute! <:TeriCelebrate:676915184698130469>"
            )
            await winner.add_roles(MUTED_ROLE, reason="Guessed the number")
            await sleep(60)
            await winner.remove_roles(MUTED_ROLE, reason="Have mercy")
        else:
            await ctx.send("No one has won.")


def setup(client):
    client.add_cog(Guess(client))
