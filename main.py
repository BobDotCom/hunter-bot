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
import logging
import os
import re
import time
from itertools import batched

import discord
from discord import ApplicationContext, Intents, option
from discord.ext.pages import Paginator

from bot.core import Bot
from dotenv import load_dotenv

from bot.hunter import Hunter
from bot.prefix import get_prefix

load_dotenv()

logging.basicConfig(
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    level=logging.INFO,
)

intents = Intents.all()
# bot = Bot(
#     command_prefix="!",
#     intents=intents,
#     proxy=os.getenv("BOT_PROXY_URL"),  # TODO: remove
# )
bot = Bot(
    command_prefix=get_prefix,
    description="hunter-bot - A discord bot for hunter written in pycord",
    debug_guilds=None,  # TODO: Remove
    intents=intents,
    strip_after_prefix=True,
    allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=False),
    activity=Bot.pick_activity(),
    proxy=os.getenv("BOT_PROXY_URL"),  # TODO: remove
)

bot.load_all_extensions()


@bot.event
async def on_connect():
    # Override the default on_connect so it won't sync commands.
    pass


if __name__ == "__main__":
    with open(os.getenv("BOT_TOKEN_FILE"), "r") as f:
        bot.run(f.read().strip())
