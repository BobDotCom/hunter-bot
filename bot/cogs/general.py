"""
hunter-bot - A discord bot for hunter written in pycord
Copyright (C) 2024  BobDotCom

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from discord import command, ApplicationContext, slash_command
from discord.ext.commands import Cog
from ..core import Bot
from ..models import Ping
from ..utils import embed, Timer


class General(Cog):
    """General commands"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @slash_command()
    async def ping(self, ctx: ApplicationContext):
        """
        Get the latency of the bot.

        Parameters
        ----------
        ctx: Ctx
            The context of the command.
        """
        gateway = ctx.bot.latency * 1000
        database = await Ping.get_latency()

        em = embed(
            title="Pong!"
        )
        em.add_field(name="Round-Trip", value="Calculating...")
        em.add_field(name="Gateway", value=f"`{gateway:.2f}`ms")
        em.add_field(
            name="Database",
            value=f"""
            **Read:** `{database[0].total_seconds() * 1000:.2f}`ms
            **Write:** `{database[1].total_seconds() * 1000:.2f}`ms
            """
        )

        with Timer() as round_trip:
            await ctx.respond(embed=em)

        em.set_field_at(
            index=0,
            name=em.fields[0].name,
            value=f"`{round_trip.ms_time():.2f}`ms"
        )
        await ctx.edit(embed=em)


def setup(bot: Bot) -> None:
    return bot.add_cog(General(bot))
