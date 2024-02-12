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
import time
from typing import Any, Self

from collections.abc import Sequence

import discord

__all__ = "var_to_title", "Timer", "humanize_sequence", "paginate_string", "embed", "error_embed"


class Timer:
    """
    A timer.
    """

    def __init__(self) -> None:
        self.start: float | None = None
        self.end: float | None = None

    def __enter__(self) -> Self:
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self.end = time.perf_counter()

    def value(self) -> datetime.timedelta:
        """
        Returns the time elapsed during the timer.

        Returns
        -------
        datetime.timedelta
            The time elapsed during the timer.
        """
        if self.start is None or self.end is None:
            raise RuntimeError("Timer has not been started or has not been ended.")
        return datetime.timedelta(seconds=self.end - self.start)

    def ms_time(self) -> float:
        """
        Returns the time elapsed during the timer in milliseconds.

        Returns
        -------
        float
            The time elapsed during the timer in milliseconds.
        """
        return self.value().total_seconds() * 1000


def paginate_string(value: str, n: int) -> list[str]:
    """
    Takes an input string and splits it along newlines into parts of length <= n.

    Parameters
    ----------
    value: str
        The string to paginate
    n: int
        The maximum length of each string

    Returns
    -------
    list[str]
        The list of paginated strings
    """
    output: list[list[str]] = [[]]
    input_val = value.splitlines()

    def page_sum(p: list[str] = None, next_item: str = None) -> int:
        # Return sum of all line lengths, plus a newline between each line
        if p is None:
            p = output[-1]
        if next_item is not None:
            p = p + [next_item]
        return sum(map(len, p)) + max(len(p) - 1, 0)

    def paginate_next(next_line: str) -> None:
        if len(next_line) > n:
            # The current line is too long to fit on a single page.
            # Take what we can and give the rest to the next page.
            if page_sum() + 1 >= n:
                # This page is full
                output.append([])

            amount = n - page_sum(next_item="")
            output[-1].append(next_line[:amount])
            paginate_next(next_line[amount:])
        elif page_sum(next_item=next_line) <= n:
            output[-1].append(next_line)
        else:
            output.append([next_line])

    for line in input_val:
        paginate_next(line)

    return ["\n".join(page) for page in output]


def var_to_title(var_name: str) -> str:
    """
    Converts a variable name to a title.

    Parameters
    ----------
    var_name: str
        The variable name to convert.

    Returns
    -------
    str
        The converted title.
    """
    return var_name.replace("_", " ").title()


def humanize_sequence(seq: Sequence[str]) -> str:
    """
    Humanizes a sequence of strings.

    Parameters
    ----------
    seq: Sequence[str]
        The sequence of strings to humanize.

    Returns
    -------
    str
        The humanized sequence.
    """
    if len(seq) == 0:
        return ""
    if len(seq) == 1:
        return seq[0]
    if len(seq) == 2:
        return f"{seq[0]} and {seq[1]}"
    return ", ".join(seq[:-1]) + ", and " + seq[-1]


def embed(**kwargs) -> discord.Embed:
    kwargs.setdefault("color", discord.Color.blurple())
    return discord.Embed(**kwargs)


def error_embed(description: str, **kwargs) -> discord.Embed:
    kwargs.setdefault("color", discord.Color.red())
    kwargs.setdefault("title", "Error")
    return discord.Embed(
        description=description,
        **kwargs
    )
