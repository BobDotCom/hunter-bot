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
        def make_embed():
            em = embed(
                title="Hunter Status",
                description=self.bot.hunter.container.status.title() if self.bot.hunter.exists else "Unavailable",
            )
            if self.bot.hunter.config is not None:
                em.add_field(
                    name="Scenario",
                    value=self.bot.hunter.config.scenario.title(),
                ),
                em.add_field(
                    name="GCI",
                    value=self.bot.hunter.config.gci,
                )
                em.add_field(
                    name="Hostility",
                    value=self.bot.hunter.config.hostility,
                )
                em.add_field(
                    name="Human Defenders",
                    value=self.bot.hunter.config.human_defenders,
                )
            return em

        class MyView(View):
            async def on_timeout(self):
                self.disable_all_items()
                await self.message.edit(embed=make_embed(), view=self)

            def update_buttons(self):
                for child in self.children:
                    if not isinstance(child, Button):
                        continue
                    match child.label.casefold():
                        case "start":
                            child.disabled = ctx.bot.hunter.running or not ctx.bot.hunter.exists
                        case ("restart" | "stop"):
                            child.disabled = not ctx.bot.hunter.running

            @button(
                label="Start",
                style=discord.ButtonStyle.green,
                emoji="▶",
                disabled=self.bot.hunter.running or not self.bot.hunter.exists,
            )
            async def start_button(self, b, interaction):
                ctx.bot.hunter.start()
                self.update_buttons()
                await interaction.response.send_message(
                    f"Starting hunter (requested by {interaction.user.mention})"
                )
                await self.message.edit(embed=make_embed(), view=self)

            @button(
                label="Restart",
                style=discord.ButtonStyle.primary,
                emoji="🔄",
                disabled=not self.bot.hunter.running,
            )
            async def restart_button(self, b, interaction):
                ctx.bot.hunter.restart()
                self.update_buttons()
                await interaction.response.send_message(
                    f"Restarting hunter (requested by {interaction.user.mention})"
                )
                await self.message.edit(embed=make_embed(), view=self)

            @button(
                label="Stop",
                style=discord.ButtonStyle.red,
                emoji="⏹",
                disabled=not self.bot.hunter.running,
            )
            async def stop_button(self, b, interaction):
                ctx.bot.hunter.stop()
                self.update_buttons()
                await interaction.response.send_message(
                    f"Stopping hunter (requested by {interaction.user.mention})"
                )
                await self.message.edit(embed=make_embed(), view=self)

        view = MyView(timeout=120)
        view.message = await ctx.respond(embed=make_embed(), view=view)


def setup(bot: Bot) -> None:
    return bot.add_cog(Hunter(bot))
