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

from discord import Message
from discord.ext import commands

from .core import Bot

__all__ = ("get_prefix", "prefix_for")


async def get_prefix(bot: Bot, message: Message) -> list[str]:
    """
    Gets the prefix for a particular message, including the bots default prefix(es) and when_mentioned.

    Parameters
    ----------
    bot: Bot
        The bot instance.
    message: Message
        The message to get the prefix for.

    Returns
    -------
    Iterable[str]
        The possible prefixes for the message.
    """
    prefixes = (await prefix_for(bot, message)) + bot.default_prefixes
    # Ignore type because mypy is straight up wrong. No idea why.
    return commands.when_mentioned_or(*prefixes)(bot, message)


async def prefix_for(bot: Bot, message: Message) -> tuple[str, ...]:
    """
    Gets the prefix for a particular message.

    Parameters
    ----------
    bot: Bot
        The bot instance.
    message: Message
        The message to get the prefix for.

    Returns
    -------
    Iterable[str]
        The possible prefixes for the message.
    """
    # Let's make some assertions, just to make the linters happy.
    if message.guild == bot.home_guild:
        return (".",)

    return tuple()
