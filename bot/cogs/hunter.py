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

import discord
from discord import command, ApplicationContext, slash_command, option, SlashCommandGroup
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.pages import Paginator
from discord.ui import View, button, Button
from docker.errors import APIError

from ..core import Bot
from ..error import WarningExc, ErrorExc, InfoExc
from ..hunter import HunterConfig, available_scenarios
from ..models import Ping
from ..utils import embed, Timer


async def _run_hunter(
        ctx: ApplicationContext,
        scenario: str,
        gci: bool = False,
        hostility: str = "0_0_0_0_0",
        human_defenders: str = ""
):
    try:
        if ctx.bot.hunter.running:
            raise InfoExc("Hunter is already running!")
        config = HunterConfig(
            scenario=scenario,
            gci=gci,
            hostility=hostility,
            human_defenders=human_defenders,
        )
        ctx.bot.hunter.run(config)
        await ctx.respond(f"Starting hunter in `{scenario}`")
    except APIError as e:
        raise ErrorExc(
            "Could not start session. Likely the docker daemon is disconnected, please contact the owner of this bot"
        ) from e


async def _stop_hunter(ctx: ApplicationContext):
    if not ctx.bot.hunter.running:
        raise InfoExc("Hunter is not running yet!")
    ctx.bot.hunter.stop()
    await ctx.respond("Hunter is stopping")


class Hunter(Cog):
    """Hunter commands"""

    hunter_group = SlashCommandGroup("hunter", "Hunter-related commands")

    def __init__(self, bot: Bot):
        self.bot = bot

    @hunter_group.command()
    @option("scenario", choices=available_scenarios)
    async def run(
            self,
            ctx: ApplicationContext,
            scenario: str,
            gci: bool = False,
            hostility: str = "0_0_0_0_0",
            human_defenders: str = ""
    ):
        await _run_hunter(ctx, scenario, gci=gci, hostility=hostility, human_defenders=human_defenders)

    @hunter_group.command()
    async def stop(self, ctx: ApplicationContext):
        # TODO: Should this be tied to the user that started hunter?
        await _stop_hunter(ctx)

    @hunter_group.command()
    @commands.is_owner()
    async def logs(self, ctx: ApplicationContext):
        # TODO: Make private
        if not self.bot.hunter.exists:
            raise InfoExc("Hunter container unavailable!")
        paginator = Paginator(
            pages=list(map(lambda _: f"```{"".join(_)}```", batched(self.bot.hunter.logs(), n=1994)))
        )
        await paginator.respond(ctx.interaction, ephemeral=True)
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
