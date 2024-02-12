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
import os

__all__ = ("Snowflake",)

from typing import Self


class Increment:
    """An incrementing counter"""

    def __init__(self) -> None:
        self.value = 0

    def __call__(self) -> int:
        self.value += 1
        return self.value

    def reset(self) -> None:
        """Reset the counter"""
        self.value = 0


class Snowflake:
    """
    The number of milliseconds since the epoch.
    """
    EPOCH = datetime.datetime(year=2024, month=1, day=1, tzinfo=datetime.timezone.utc)
    _INCREMENT = Increment()

    def __init__(self, value: int) -> None:
        """A snowflake

        Parameters
        ----------
        value: int
            The value of the snowflake
        """
        self.value = value

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.value}>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Snowflake) and self.value == other.value

    def __lt__(self, other: object) -> bool:
        return isinstance(other, Snowflake) and self.value < other.value

    def __le__(self, other: object) -> bool:
        return isinstance(other, Snowflake) and self.value <= other.value

    def __ge__(self, other: object) -> bool:
        return isinstance(other, Snowflake) and self.value >= other.value

    def __gt__(self, other: object) -> bool:
        return isinstance(other, Snowflake) and self.value > other.value

    def __ne__(self, other: object) -> bool:
        return isinstance(other, Snowflake) and self.value != other.value

    def __hash__(self) -> int:
        return hash(self.value)

    @property
    def timestamp(self) -> int:
        """The timestamp of the snowflake. This is the number of milliseconds since the epoch."""
        return self.value >> 22

    @property
    def worker_id(self) -> int:
        """The worker id of the snowflake. This is a unique identifier of the worker that created the snowflake."""
        return (self.value & 0x3E0000) >> 17

    @property
    def process_id(self) -> int:
        """The process id of the snowflake. This is a unique identifier of the process that created the snowflake."""
        return (self.value & 0x1F000) >> 12

    @property
    def increment(self) -> int:
        """The increment of the snowflake. This is a number incremented once for each object created during runtime on
        the current process.
        """
        return self.value & 0xFFF

    def ago(self) -> datetime.timedelta:
        """The time since the snowflake was created.

        Returns
        -------
        datetime.timedelta
            The time since the snowflake was created
        """
        return datetime.datetime.now(datetime.timezone.utc) - self.datetime()

    def datetime(self) -> datetime.datetime:
        """The datetime of the snowflake. This is the number of milliseconds since the epoch.

        Returns
        -------
        datetime.datetime
            The datetime of the snowflake
        """
        return Snowflake.EPOCH + datetime.timedelta(milliseconds=self.timestamp)

    @classmethod
    def from_values(cls, timestamp: int, worker_id: int, process_id: int, increment: int) -> Self:
        """A snowflake

        Parameters
        ----------
        timestamp: int
            The timestamp of the snowflake. This is the number of milliseconds since the epoch.
        worker_id: int
            The worker id of the snowflake. This is a unique identifier of the worker that created the snowflake.
        process_id: int
            The process id of the snowflake. This is a unique identifier of the process that created the snowflake.
        increment: int
            The increment of the snowflake. This is a number incremented once for each object created during runtime on
            the current process.
        """
        return cls(timestamp << 22 | worker_id << 17 | process_id << 12 | increment)

    @classmethod
    def new(cls) -> Self:
        """Create a new snowflake

        Returns
        -------
        Snowflake
            A new snowflake
        """
        return cls.from_values(
            timestamp=round((datetime.datetime.now(datetime.UTC) - cls.EPOCH).total_seconds() * 10 ** 3),
            worker_id=1,
            process_id=os.getpid(),
            increment=cls._INCREMENT(),
        )
