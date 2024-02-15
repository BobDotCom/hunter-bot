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
import datetime
import logging
import os
import random
import traceback
from itertools import batched
from typing import Any
import re

from discord import Intents, ApplicationContext, option, ApplicationCommandError, Permissions, Message, \
    Activity, ActivityType, Object, Guild, Forbidden
from discord.utils import copy_doc, get_or_fetch
from tortoise import Tortoise

from .error import BaseError, InfoExc, ErrorExc, BotPermissionError
from discord.ext.pages import Paginator
# from git import Repo  # type: ignore
from discord.ext.commands import Bot as _Bot, CommandError, CommandNotFound, MissingRequiredArgument, UserInputError, \
    BotMissingPermissions, Context, CheckFailure, MissingRole

from .hunter import Hunter

_log = logging.getLogger(__name__)


class Bot(_Bot):
    default_prefixes = "h.", "hunter."
    extensions_to_load = "general", "hunter"
    home_guild: Object | Guild = Object(id=742628032111706194)

    def __init__(self, *args: Any, **kwargs: Any) -> None:

        super().__init__(*args, **kwargs)
        self.listeners: Listeners = Listeners(self)
        self.start_time = datetime.datetime.now(datetime.timezone.utc)
        # self.version_info = VersionInfo.from_repo()
        self.load_jsk()
        self.hunter = Hunter(os.getenv("HUNTER_VERSION"))
        self.hunter.pull()
        # try:
        #     self.hunter.pull()
        # except:
        #     _log.exception("Hunter pull failed")

    def load_jsk(self) -> None:
        """
        Configures and loads jishaku.
        """
        os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
        os.environ['JISHAKU_RETAIN'] = "True"
        # self.owner_id = None
        self.owner_ids = {
            690420846774321221,  # @bobdotcom
            380086540073959434,  # @vanosten
            218638666329751552,  # @.pinto
        }
        self.load_extension("jishaku")

    def uptime(self) -> datetime.timedelta:
        """
        Returns the uptime of the bot.

        Returns
        -------
        datetime.timedelta
            The uptime of the bot.
        """
        return datetime.datetime.now(datetime.timezone.utc) - self.start_time

    def load_all_extensions(self) -> None:
        """
        Loads extensions.
        """
        for extension in self.extensions_to_load:
            name = f"bot.cogs.{extension}"
            if name not in self.extensions:
                self.load_extension(name)

    def reload_all_extensions(self) -> None:
        """
        Reloads extensions.
        """
        for extension in self.extensions_to_load:
            name = f"bot.cogs.{extension}"
            if name in self.extensions:
                self.reload_extension(name)

    def unload_all_extensions(self) -> None:
        """
        Unloads extensions.
        """
        for extension in self.extensions_to_load:
            name = f"bot.cogs.{extension}"
            if name in self.extensions:
                self.unload_extension(name)

    @classmethod
    async def setup_database(cls) -> None:
        """
        Sets up the database.
        """
        models = "core", "ping"
        # await tortoise.init(
        #     {
        #         "connections": {
        #             "default": {
        #                 "engine": "tortoise.backends.sqlite",
        #                 "credentials": {
        #                     "file_path": f"{cls.storage_dir}/main.db",
        #                 },
        #         }
        #     }
        # )
        # storage_dir = "storage"
        with open(os.getenv("POSTGRES_PASSWORD_FILE"), "r") as f:
            password = f.read().strip()

        await Tortoise.init(
            # db_url=f'sqlite://{storage_dir}/main.db',
            db_url=f"postgres://postgres:{password}@{os.getenv("POSTGRES_HOST")}:5432/{os.getenv("POSTGRES_DB")}",
            modules={'models': [f'bot.models.{model}' for model in models]},
        )

        await Tortoise.generate_schemas()

    @copy_doc(_Bot.start)
    async def start(self, token: str, *, reconnect: bool = True) -> None:
        """
        Starts the bot, and sets up the database.
        """
        await self.setup_database()
        await super().start(token, reconnect=reconnect)

    async def close(self) -> None:
        """
        Closes the bot, and cleans up the database connection.
        """
        await Tortoise.close_connections()
        await super().close()

    @staticmethod
    def pick_activity() -> Activity:
        """
        Picks an activity (status) for the bot

        Returns
        -------
        Activity
            The status for the bot
        """
        statuses = {
            ActivityType.watching: [
                "the world",
                "the stars"
            ],
            ActivityType.listening: [
                "the radio",
            ],
            ActivityType.playing: [
                "with a ball",
            ],
        }
        vals, weights = [], []
        for key, val in statuses.items():
            vals.append(key)
            weights.append(len(val))

        status_type = random.choices(vals, weights=weights, k=1)[0]
        status = random.choice(statuses[status_type])

        return Activity(
            name=status,
            type=status_type,
        )


class Listeners:
    """
    Listeners for the bot.

    Parameters
    ----------
    bot: Bot
        The bot to register the listeners to.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        listeners = (
            "connect",
            "ready",
            "disconnect",
            "reconnect",
            "message_edit",
            "command_error",
            "application_command_error",
        )
        for listener in listeners:
            bot.add_listener(getattr(self, f"on_{listener}"), f"on_{listener}")

    @staticmethod
    async def on_connect() -> None:
        """
        Connect handler
        """
        print("Connected to discord. Registering commands and waiting for READY...")

    async def on_ready(self) -> None:
        """
        Ready handler
        """
        print(f"Ready. Logged in as {self.bot.user}")
        if isinstance(self.bot.home_guild, Object):
            try:
                self.bot.home_guild = await get_or_fetch(self.bot, "guild", self.bot.home_guild.id)
            except Forbidden:
                _log.error("Failed to fetch home guild, bot is not in server")

    @staticmethod
    async def on_disconnect() -> None:
        """
        Disconnect handler
        """
        print("Disconnected from discord.")

    @staticmethod
    async def on_reconnect() -> None:
        """
        Reconnect handler
        """
        print("Reconnected to discord. Waiting for READY...")

    async def on_message_edit(self, before: Message, after: Message) -> None:
        """
        Message edit handler
        """
        if before.content != after.content:
            await self.bot.process_commands(after)

    @classmethod
    async def _command_error(cls, ctx: Context | ApplicationContext, error: CommandError | ApplicationCommandError) -> None:
        """
        Command error handler
        """
        if isinstance(original := getattr(error, "original", None), BaseError):
            await original.handle(ctx)
        else:
            try:
                if isinstance(error, BotMissingPermissions):
                    raise BotPermissionError(Permissions(**{p: True for p in error.missing_permissions}))
                if isinstance(error, UserInputError):
                    if isinstance(error, MissingRequiredArgument):
                        if ((prefix := getattr(ctx, "prefix", None)) is not None
                                and (command := getattr(ctx, "command", None)) is not None):
                            raise InfoExc(
                                f"`{error.param.name}` is a required argument that is missing.",
                                recommendation_title="Usage",
                                recommendation=f"`{prefix}{command.qualified_name} {command.signature}`",
                            )
                        raise ErrorExc(
                            "Missing required argument. While handling this error, another error occurred.",
                        )
                    raise InfoExc(error.args[0])

                if isinstance(error, CheckFailure):
                    if isinstance(error, MissingRole):
                        # The default message is fine, but if missing_role is a snowflake, make it a mention
                        if isinstance(error.missing_role, int):
                            error = MissingRole(f"<@&{error.missing_role}>")

                    raise InfoExc(error.args[0])

                if isinstance(error, CommandNotFound):
                    return
                traceback.print_exception(type(error), error, error.__traceback__)
            except BaseError as exc:
                mock_cmd_error = CommandError("Mock command error")
                mock_cmd_error.original = exc  # type: ignore[attr-defined]
                await cls._command_error(ctx, mock_cmd_error)

    @classmethod
    async def on_command_error(cls, ctx: Context, error: CommandError) -> None:
        """
        Command error handler
        """
        await cls._command_error(ctx, error)

    @classmethod
    async def on_application_command_error(cls, ctx: ApplicationContext, error: ApplicationCommandError) -> None:
        """
        Application command error handler
        """
        await cls._command_error(ctx, error)
