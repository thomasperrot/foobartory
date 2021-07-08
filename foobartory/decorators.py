import functools
import logging
from typing import TYPE_CHECKING, Awaitable, Callable

if TYPE_CHECKING:
    from foobartory.models import Robot

logger = logging.getLogger(__name__)


def activity(func: Callable[["Robot"], Awaitable]):
    """A decorator to add a check before performing an activity.

    When a robot is changing its current activity, it must sleep for several seconds.
    """

    @functools.wraps(func)
    async def wrapper(self: "Robot"):
        await self.check_activity(func.__name__)
        await func(self)
        if not self._stopped:
            logger.info("[*] %s did %s", self, func.__name__)
            logger.debug(self._factory)

    return wrapper
