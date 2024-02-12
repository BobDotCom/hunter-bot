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
import random
import traceback
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import TYPE_CHECKING, TypeVar, Any, Self

from discord import Permissions, ApplicationContext, Embed
from discord.colour import Color

__all__ = "ErrorSeverity", "BaseError", "InfoExc", "WarningExc", "ErrorExc", "CriticalExc", "BotPermissionError"

from .utils import humanize_sequence, var_to_title, embed, error_embed


class ErrorSeverity(IntEnum):
    """
    Enum for error severity.
    """
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3

    @property
    def default_value(self) -> Self:
        """
        Returns the default error severity.
        """
        return ErrorSeverity.ERROR

    def get_message(self) -> str:
        """
        Returns the message for the error severity. This is used for embed titles.

        Returns
        -------
        str
            The message for the error severity.
        """
        match self.value:
            case self.INFO:
                return "Something isn't quite right..."
            case self.WARNING:
                return random.choice(("Oh no!", "Oops!", "Uh oh!"))
            case self.ERROR:
                return "Something went wrong..."
            case self.CRITICAL:
                return "⚠️ ERROR! ⚠️"
            case _:
                return self.default_value.get_message()  # type: ignore[no-any-return]

    def get_color(self) -> Color:
        """
        Returns the color for the error severity. This is used for embed colors.

        Returns
        -------
        Color
            The color for the error severity.
        """
        match self.value:
            case self.INFO:
                return Color.blue()
            case self.WARNING:
                return Color.yellow()
            case self.ERROR | self.CRITICAL:
                return Color.red()
            case _:
                return self.default_value.get_color()  # type: ignore[no-any-return]

    def should_propagate(self) -> bool:
        """
        Returns a boolean representing whether an error of this severity should propagate to an error handler.

        Returns
        -------
        bool
            Whether an error of this severity should propagate to an error handler.
        """
        match self.value:
            case self.INFO | self.WARNING | self.ERROR:
                return False
            case self.CRITICAL:
                return True
            case _:
                return self.default_value.should_propagate()  # type: ignore[no-any-return]

    def is_fatal(self) -> bool:
        """
        Returns a boolean representing whether an error of this severity is fatal.

        Returns
        -------
        bool
            Whether an error of this severity is fatal.
        """
        match self.value:
            case self.INFO | self.WARNING:
                return False
            case self.ERROR | self.CRITICAL:
                return True
            case _:
                return self.default_value.is_fatal()  # type: ignore[no-any-return]


class BaseError(ABC, Exception):
    """
    Base class for all errors.
    """

    def __init__(
            self,
            message: str,
            severity: ErrorSeverity | None = None,
            *,
            recommendation: str | None = None,
            recommendation_title: str | None = None,
            ephemeral_response: bool | None = None,
    ) -> None:
        """
        Initializes the error.

        Parameters
        ----------
        message: str
            The message for the error.
        severity: ErrorSeverity
            The severity of the error. Defaults to _default_severity.
        """
        super().__init__(message)
        if severity is None:
            severity = self._default_severity()
        self.message = message
        self.severity: ErrorSeverity = severity
        self.recommendation = recommendation
        self.recommendation_title = recommendation_title
        if ephemeral_response is None:
            self.ephemeral_response = self._ephemeral_response()
        else:
            self.ephemeral_response = ephemeral_response

    @staticmethod
    @abstractmethod
    def _default_severity() -> ErrorSeverity:
        """
        Returns the default severity for the error.

        Returns
        -------
        ErrorSeverity
            The default severity for the error.
        """
        raise NotImplementedError

    @staticmethod
    def _ephemeral_response() -> bool:
        """
        Returns whether the error response should be ephemeral.

        Returns
        -------
        bool
            Whether the error response should be ephemeral.
        """
        return False

    def get_embed(self, ctx: ApplicationContext | None) -> Embed:
        """
        Returns the embed for the error.

        Returns
        -------
        dict
            The embed for the error.
        """
        em = error_embed(
            self.message,
            title=self.severity.get_message(),
            color=self.severity.get_color(),
            # ctx=ctx
        )
        if self.recommendation is not None:
            em.add_field(
                name=self.recommendation_title,
                value=self.recommendation,
                inline=False,
            )
        return em  # type: ignore[no-any-return]

    def should_propagate(self) -> bool:
        """
        Returns whether the error should propagate to an error handler.

        Returns
        -------
        bool
            Whether or not the error should propagate.
        """
        return self.severity.should_propagate()

    def is_fatal(self) -> bool:
        """
        Returns whether the error represents a fatal exception.

        Returns
        -------
        bool
            Whether or not the error is fatal.
        """
        return self.severity.is_fatal()

    async def handle(self, ctx: ApplicationContext) -> None:
        """
        Handles the error.

        Parameters
        ----------
        ctx: Ctx
            The context of the error.
        """
        if (respond := getattr(ctx, "respond", None)) is not None:
            await respond(embed=self.get_embed(ctx))
        else:
            raise ErrorExc("No respond method found")
        if self.should_propagate():
            raise RuntimeError("A fatal exception occurred during execution") from self
        if self.is_fatal():
            traceback.print_exception(type(self), self, self.__traceback__)


class InfoExc(BaseError):
    """
    Represents an informational exception. This is used in situations where the user did something wrong, not indicative
    of a bug.
    """

    @staticmethod
    def _default_severity() -> ErrorSeverity:
        return ErrorSeverity.INFO


class WarningExc(BaseError):
    """
    Represents a warning exception. This is used in situations where the user did not directly do anything wrong, but
    there was a recognized failure that originates from a misconfiguration or such. This is not indicative of a bug.
    """

    @staticmethod
    def _default_severity() -> ErrorSeverity:
        return ErrorSeverity.WARNING


class ErrorExc(BaseError):
    """
    Represents an error exception. This is used in situations where the user didn't do anything wrong, but there was an
    unrecognized error in the bot. This is indicative of a bug.
    """

    @staticmethod
    def _default_severity() -> ErrorSeverity:
        return ErrorSeverity.ERROR


class CriticalExc(BaseError):
    """
    Represents a critical exception. This is used in situations where the user didn't do anything wrong, but there was a
    critical error in the bot, that could potentially cause more serious issues. This is indicative of a bug.
    """

    @staticmethod
    def _default_severity() -> ErrorSeverity:
        return ErrorSeverity.CRITICAL


class BotPermissionError(WarningExc):
    """
    Represents an error caused by a bot not having the required permissions.
    """

    def __init__(self, missing_permissions: Permissions, target: str | None = None) -> None:
        missing = humanize_sequence(
            [f'`{var_to_title(v)}`' for v in missing_permissions.VALID_FLAGS if getattr(missing_permissions, v)]
        ) + ' '
        message = f"I'm missing the {missing}permission{'s' if len(missing) != 2 else ''} to perform this action"
        if target is not None:
            message += f" on {target}"
        super().__init__(message)
