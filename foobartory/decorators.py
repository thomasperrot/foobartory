import functools
import logging
from typing import Awaitable, Callable, TYPE_CHECKING


if TYPE_CHECKING:
    from foobartory.models import Robot


def activity(func: Callable[["Robot"], Awaitable]):
    """A decorator to add a check before performing an activity.

    When a robot is changing its current activity, it must sleep for several seconds.
    """

    @functools.wraps(func)
    async def wrapper(self):
        await self.check_activity(func.__name__)
        await func(self)
        if not self._stopped:
            logging.info("[*] %s did %s", self, func.__name__)
            logging.debug(self._factory)

    return wrapper
