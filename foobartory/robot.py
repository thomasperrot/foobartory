import asyncio
import functools
from enum import Enum
from dataclasses import dataclass
import random
import uuid
from typing import Callable

ROBOT_COST_EUROS = 3
ROBOT_COST_FOO = 6
SWITCH_ACTIVITY_DELAY = 5
FOO_MINING_DELAY = 1
BAR_MINING_MIN_DELAY = 0.5
BAR_MINING_MAX_DELAY = 2
FOOBAR_PRICE = 1
FOOBAR_SUCCESS_RATE = 0.6
FOOBAR_CREATION_DELAY = 2
FOOBAR_SELL_MAX = 5
FOOBAR_SELL_DELAY = 10


class CannotCreateFoobarError(Exception):
    pass


class CannotBuyRobotError(Exception):
    pass


class Foo:
    def __init__(self) -> None:
        self.id = uuid.uuid4()


class Bar:
    def __init__(self) -> None:
        self.id = uuid.uuid4()


class FooBar:
    def __init__(self, foo: Foo, bar: Bar) -> None:
        self.foo_id = foo.id
        self.bar_id = bar.id


def activity(func):
    @functools.wraps(func)
    async def wrapper(self):
        if self._activity != func:
            await self.change_activity(func)
        return await func(self)
    return wrapper


class Robot:
    def __init__(self, factory: "Factory") -> None:
        self._activity = self.harvest_foo
        self._factory = factory

    async def run(self) -> None:
        while self._factory.account < 30:
            print(self._factory.account)

            if self._factory.account >= ROBOT_COST_EUROS:
                if self._factory.foo_queue.qsize() >= ROBOT_COST_FOO:
                    await self.buy_robot()
                else:
                    await self.harvest_foo()

            elif self.must_sell_foobar:
                await self.sell_foobar()

            elif self.must_create_foobar:
                await self.create_foobar()

            elif self.must_harvest_bar:
                await self.harvest_bar()

            else:
                await self.harvest_foo()

    async def change_activity(self, activity: Callable) -> None:
        await asyncio.sleep(5)
        self._activity = activity

    @property
    def must_sell_foobar(self) -> bool:
        """Robot must sell Foobar as soon as Foobar is available if no other
        robot is already selling Foobar.
        """

        return self._factory.foobar_queue.empty() and not self._factory.sell_foobar_lock.locked()

    @property
    def must_create_foobar(self) -> bool:
        """Robot must create Foobar as soon as Foo and Bar are available."""

        return not self._factory.foo_queue.empty() and not self._factory.bar_queue.empty()

    @property
    def must_harvest_bar(self) -> bool:
        """Robot must harvest Bar until we have 10."""

        return self._factory.bar_queue.qsize() < 10

    @activity
    async def harvest_foo(self) -> None:
        await asyncio.sleep(FOO_MINING_DELAY)
        self._factory.foo_queue.put_nowait(Foo())

    @activity
    async def harvest_bar(self) -> None:
        delay = random.uniform(BAR_MINING_MIN_DELAY, BAR_MINING_MAX_DELAY)
        await asyncio.sleep(delay)
        self._factory.bar_queue.put_nowait(Bar())

    @activity
    async def create_foobar(self) -> None:
        try:
            foo = self._factory.foo_queue.get_nowait()
            bar = self._factory.bar_queue.get_nowait()
        except asyncio.QueueEmpty():
            raise CannotCreateFoobarError()

        await asyncio.sleep(FOOBAR_CREATION_DELAY)
        if random.random() <= FOOBAR_SUCCESS_RATE:
            self._factory.foo_queue.put_nowait(FooBar(foo, bar))
        else:
            self._factory.bar_queue.put_nowait(bar)

    @activity
    async def sell_foobar(self) -> None:
        async with self._factory.sell_foobar_lock:
            await asyncio.sleep(FOOBAR_SELL_DELAY)
            for _ in range(FOOBAR_SELL_MAX):
                try:
                    self._factory.foobar_queue.get_nowait()
                except asyncio.QueueEmpty():
                    break
                else:
                    self._factory.account += FOOBAR_PRICE

    @activity
    def buy_robot(self) -> None:
        if self._factory.account < ROBOT_COST_EUROS:
            raise CannotBuyRobotError(
                f"You need 3€ to buy a new robot, you currently have "
                f"{self._factory.account}"
            )
        if self._factory.foo_queue.qsize() < ROBOT_COST_FOO:
            raise CannotBuyRobotError(
                f"You need 6 Foo to buy a new robot, you currently have "
                f"{self._factory.foo_queue.qsize()}"
            )
        self._factory.account -= ROBOT_COST_EUROS
        for _ in range(ROBOT_COST_EUROS):
            self._factory.foo_queue.get_nowait()
        robot = Robot(factory=self._factory)
        self._factory.robots.append(robot)
        asyncio.ensure_future(robot.run())


class Factory:
    def __init__(self) -> None:
        self.robots = [Robot(factory=self), Robot(factory=self)]
        self.account = 0

        # queues
        self.foo_queue = asyncio.Queue()
        self.bar_queue = asyncio.Queue()
        self.foobar_queue = asyncio.Queue()

        # locks
        self.sell_foobar_lock = asyncio.Lock()


if __name__ == '__main__':
    factory = Factory()
    tasks = [robot.run() for robot in factory.robots]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*tasks))
