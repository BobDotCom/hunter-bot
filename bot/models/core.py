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
from typing import Union, TypeVar, TYPE_CHECKING

from discord.guild import Guild as _Guild
from discord.member import Member
from discord.user import User as _User
from tortoise import Model  # type: ignore[attr-defined]
from tortoise.fields import BigIntField, ForeignKeyRelation

from typing import Self

G = TypeVar('G', bound=_Guild)
U = TypeVar('U', bound=Union[_User, Member])

__all__ = "DBGuild", "DBUser"

# if TYPE_CHECKING:
#     from .highlight import HighlightList
#     from .tag import Tag
# else:
#     HighlightList = TypeVar('HighlightList', bound=Model)
#     Tag = TypeVar('Tag', bound=Model)


class DBGuild(Model):  # type: ignore[misc]
    """
    A guild in the database.
    """
    id = BigIntField(pk=True)
    # lists: ForeignKeyRelation[HighlightList]
    # tags: ForeignKeyRelation[Tag]

    @classmethod
    async def from_guild(cls, guild: G, allow_create: bool = True) -> Self:
        """
        Get a guild from the database, taking a discord.Guild object.

        Parameters
        ----------
        guild: discord.Guild
            The guild to get.
        allow_create: bool
            Whether to create the guild if it doesn't exist. Defaults to True.
        """
        if allow_create:
            return (await cls.get_or_create(id=guild.id))[0]
        return await cls.get(id=guild.id)


class DBUser(Model):  # type: ignore[misc]
    """
    A user in the database.
    """
    id = BigIntField(pk=True)
    # lists: ForeignKeyRelation[HighlightList]
    # tags: ForeignKeyRelation[Tag]

    @classmethod
    async def from_user(cls, user: U, allow_create: bool = True) -> Self:
        """
        Get a user from the database, taking a discord.User or discord.Member object.

        Parameters
        ----------
        user: discord.User | discord.Member
            The user to get.
        allow_create: bool
            Whether to create the user if it doesn't exist. Defaults to True.
        """
        if allow_create:
            return (await cls.get_or_create(id=user.id))[0]
        return await cls.get(id=user.id)
