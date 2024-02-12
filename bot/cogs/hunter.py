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
import os
import re
from itertools import batched

from discord import command, ApplicationContext, slash_command, option, SlashCommandGroup
from discord.ext.commands import Cog
from discord.ext.pages import Paginator

from ..core import Bot
from ..error import WarningExc
from ..models import Ping
from ..utils import embed, Timer


scenario_dir = f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))}/hunter-scenarios"
available_scenarios = list(
    map(
        lambda scenario: scenario[9:-3],
        filter(lambda scenario: re.match(r"scenario_\w+\.py", scenario), os.listdir(scenario_dir))
    )
)


async def _start_hunter(ctx: ApplicationContext, scenario: str):
    try:
        if ctx.bot.hunter.running:
            return await ctx.respond("Hunter is already running!")
        ctx.bot.hunter.start(scenario)
        await ctx.respond(f"Starting hunter in `{scenario}`")
    except:
        raise WarningExc("Docker daemon is disconnected, please contact the owner of this bot")


async def _stop_hunter(ctx: ApplicationContext):
    if not ctx.bot.hunter.running:
        return await ctx.respond("Hunter is not running yet!")
    ctx.bot.hunter.stop()
    await ctx.respond("Hunter is stopping")


class Hunter(Cog):
    """Hunter commands"""

    hunter_group = SlashCommandGroup("hunter", "Hunter-related commands")

    def __init__(self, bot: Bot):
        self.bot = bot

    @hunter_group.command()
    @option("scenario", choices=available_scenarios)
    async def start(self, ctx: ApplicationContext, scenario):
        await _start_hunter(ctx, scenario)

    @hunter_group.command()
    async def stop(self, ctx: ApplicationContext):
        # TODO: Should this be tied to the user that started hunter?
        await _stop_hunter(ctx)

    @hunter_group.command()
    async def logs(self, ctx: ApplicationContext):
        # TODO: Make private
        if not ctx.bot.hunter.running:
            return await ctx.respond("Hunter is not running!")
        paginator = Paginator(
            pages=list(map(lambda _: "".join(_), batched(ctx.bot.hunter.logs().decode("utf-8"), n=2000)))
        )
        await paginator.respond(ctx.interaction)
        # await ctx.respond

    @hunter_group.command()
    async def status(self, ctx: ApplicationContext):
        # Include: Container status, started by, runtime, more?
        # Possibly: Last session details?
        return

    @slash_command()
    @option("scenario", choices=available_scenarios)
    async def start_hunter(self, ctx: ApplicationContext, scenario: str):
        await _start_hunter(ctx, scenario)

    @slash_command()
    async def stop_hunter(self, ctx: ApplicationContext):
        await _stop_hunter(ctx)


def setup(bot: Bot) -> None:
    return bot.add_cog(Hunter(bot))
