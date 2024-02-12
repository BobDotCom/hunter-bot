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
from datetime import timedelta

from tortoise import Model  # type: ignore[attr-defined]
from tortoise.exceptions import DoesNotExist
from tortoise.fields import BooleanField

from bot.utils import Timer

__all__ = ("Ping",)


class Ping(Model):  # type: ignore[misc]
    """
    Ping model
    """
    val = BooleanField(default=False)

    @classmethod
    async def get_latency(cls) -> tuple[timedelta, timedelta]:
        """
        Returns the latency of the database.

        Returns
        -------
        tuple[float, float]
            Tuple of read and write latency.
        """
        try:
            with Timer() as read_latency:
                obj = await cls.get(id=0)
        except DoesNotExist:
            await cls.create(id=0)
            with Timer() as read_latency:
                obj = await cls.get(id=0)

        obj.val = not obj.val
        with Timer() as write_latency:
            await obj.save()

        return read_latency.value(), write_latency.value()
