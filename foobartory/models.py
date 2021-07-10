import asyncio
import logging
import random
import uuid
from typing import List

import click

from foobartory import config
from foobartory.decorators import activity

logger = logging.getLogger(__name__)


class Foo:
    def __init__(self) -> None:
        self.id = uuid.uuid4()


class Bar:
    def __init__(self) -> None:
        self.id = uuid.uuid4()


class FooBar:
    def __init__(self, foo: Foo, bar: Bar) -> None:
        self.foo = foo
        self.bar = bar

    def __str__(self) -> str:
        return f"{self.foo.id} - {self.bar.id}"


class Robot:
    """A robot is autonomous actor that can:
    * Mine Foo
    * Mine Bar
    * Create FooBar from Foo and Bar
    * Sell FooBar
    * Buy a new robot

    It has its own sets of rules to decide when to perform those actions, depending on
    the factory stocks and locks.
    """

    def __init__(self, factory: "Factory") -> None:
        self._factory = factory
        self._current_activity = self.harvest_foo.__name__
        self._id = len(self._factory.robots)
        self._stopped: bool = False

    def __str__(self) -> str:
        return f"Robot {self._id}"

    async def check_activity(self, new_activity: str) -> None:
        """Check if the robot is switching activity. If so, it must sleep."""

        if new_activity != self._current_activity:
            await asyncio.sleep(config.SWITCH_ACTIVITY_DELAY / self._factory.speed)
            self._current_activity = new_activity

    async def run(self) -> None:
        """Choose what what action to perform, and perform it, until stopped."""

        while not self._stopped:

            if self.must_buy_robot:
                async with self._factory.buy_robot_lock:
                    await self.buy_robot()

            elif self.must_harvest_foo:
                await self.harvest_foo()

            elif self.must_sell_foobar:
                async with self._factory.sell_foobar_lock:
                    await self.sell_foobar()

            elif self.must_create_foobar:
                await self.create_foobar()

            else:
                await self.harvest_bar()

    def stop(self) -> None:
        self._stopped = True

    @property
    def must_harvest_foo(self) -> bool:
        """Robot must harvest Foo if they do not have enough Foo to create a Robot."""

        return self._factory.foo_queue.qsize() < config.ROBOT_COST_FOO

    @activity
    async def harvest_foo(self) -> None:
        """Put a new Foo in Foo queue."""

        await asyncio.sleep(config.FOO_MINING_DELAY / self._factory.speed)
        self._factory.foo_queue.put_nowait(Foo())

    @activity
    async def harvest_bar(self) -> None:
        """Put a new Bar in Bar queue."""

        delay = random.uniform(config.BAR_MINING_MIN_DELAY, config.BAR_MINING_MAX_DELAY)
        await asyncio.sleep(delay / self._factory.speed)
        self._factory.bar_queue.put_nowait(Bar())

    @property
    def must_create_foobar(self) -> bool:
        """Robot must create Foobar as soon as Foo and Bar are available."""

        return (
            not self._factory.foo_queue.empty() and not self._factory.bar_queue.empty()
        )

    @activity
    async def create_foobar(self) -> None:
        """Try to create a FooBar from a Foo and a Bar, and put it in FooBar queue."""

        if self._factory.foo_queue.empty() or self._factory.bar_queue.empty():
            return

        foo = self._factory.foo_queue.get_nowait()
        bar = self._factory.bar_queue.get_nowait()

        await asyncio.sleep(config.FOOBAR_CREATION_DELAY / self._factory.speed)
        if random.random() <= config.FOOBAR_SUCCESS_RATE:
            self._factory.foobar_queue.put_nowait(FooBar(foo, bar))
        else:
            self._factory.bar_queue.put_nowait(bar)

    @property
    def must_sell_foobar(self) -> bool:
        """Robot must sell Foobar if at least 3 Foobar are available if no other
        robot is already selling Foobar.
        """

        return (
            self._factory.foobar_queue.qsize() >= 3
            and not self._factory.sell_foobar_lock.locked()
        )

    @activity
    async def sell_foobar(self) -> None:
        """Get FooBars from FooBar queue, and sell them to increase the factory
        account.
        """

        await asyncio.sleep(config.FOOBAR_SELL_DELAY / self._factory.speed)
        for _ in range(config.FOOBAR_SELL_MAX):
            try:
                self._factory.foobar_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            else:
                self._factory.account += config.FOOBAR_PRICE

    @property
    def must_buy_robot(self) -> bool:
        """Robot must buy another robot if it has the correct amount of money, enough
        Foo, and if no other robot is currently buying robot."""

        return (
            self._factory.account >= config.ROBOT_COST_EUROS
            and self._factory.foo_queue.qsize() >= config.ROBOT_COST_FOO
            and not self._factory.buy_robot_lock.locked()
        )

    @activity
    async def buy_robot(self) -> None:
        """Create a new Robot, and it to the factory."""

        if (
            self._factory.account < config.ROBOT_COST_EUROS
            or self._factory.foo_queue.qsize() < config.ROBOT_COST_FOO
        ):
            return
        self._factory.account -= config.ROBOT_COST_EUROS
        for _ in range(config.ROBOT_COST_FOO):
            self._factory.foo_queue.get_nowait()
        self._factory.add_robot(Robot(factory=self._factory))


class Factory:
    """The main factory object.

    It contains all the application shared data, and offers basic control over the
    robots.
    """

    def __init__(self, speed: float = 1) -> None:
        self.speed = speed
        self.robots: List[Robot] = []
        self.account = 0

        # queues
        self.foo_queue: asyncio.Queue[Foo] = asyncio.Queue()
        self.bar_queue: asyncio.Queue[Bar] = asyncio.Queue()
        self.foobar_queue: asyncio.Queue[FooBar] = asyncio.Queue()

        # locks
        self.sell_foobar_lock = asyncio.Lock()
        self.buy_robot_lock = asyncio.Lock()

        self._stopped = True

    def __str__(self) -> str:
        return f"""robots: {len(self.robots)},
account: {self.account},
foo: {self.foo_queue.qsize()},
bar: {self.bar_queue.qsize()},
foobar: {self.foobar_queue.qsize()}"""

    def run(self) -> None:
        self._stopped = False
        asyncio.get_event_loop().run_until_complete(self._run_until_stopped())

    def add_robot(self, robot: Robot) -> None:
        self.robots.append(robot)
        if len(self.robots) == config.ROBOT_MAX_NUMBER:
            self._stop()
        else:
            click.echo(f"[*] You now have {len(self.robots)} robots")
            asyncio.ensure_future(robot.run())

    async def _run_until_stopped(self) -> None:
        while not self._stopped:
            await asyncio.sleep(0.1)

    def _stop(self) -> None:
        click.echo("[+] Congratulation, you have 30 robots!")
        self._stopped = True
        self._stop_robots()

    def _stop_robots(self) -> None:
        for robot in self.robots:
            robot.stop()
