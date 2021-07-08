import pytest

import foobartory
from foobartory.models import Bar, Foo, FooBar, Robot


def test_initial_activity(robot):
    assert robot._current_activity == "harvest_foo"


def test_robot_str(robot):
    assert str(robot) == "Robot 0"


def test_stop(robot):
    assert not robot._stopped
    robot.stop()
    assert robot._stopped


def test_must_harvest_foo(factory, robot):
    """Factory Foo queue is currently empty."""

    assert factory.foo_queue.empty()
    assert robot.must_harvest_foo


def test_stop_harvesting_foo(factory, robot):
    """Assert the robot must not harvest foo if enough Foo is in the factory."""

    for _ in range(6):
        factory.foo_queue.put_nowait(Foo())
    assert not robot.must_harvest_foo


@pytest.mark.asyncio
async def test_harvest_foo(factory, robot, mock_sleep):
    await robot.harvest_foo()

    foo = factory.foo_queue.get_nowait()
    assert isinstance(foo, Foo)
    assert factory.foo_queue.empty()
    mock_sleep.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_harvest_bar(factory, robot, mock_sleep):
    robot._current_activity = "harvest_bar"

    await robot.harvest_bar()

    bar = factory.bar_queue.get_nowait()
    assert isinstance(bar, Bar)
    assert factory.bar_queue.empty()
    mock_sleep.assert_awaited_once()
    assert 0.5 <= mock_sleep.await_args[0][0] <= 2


def test_must_create_foobar(factory, robot):
    factory.foo_queue.put_nowait(Foo())
    factory.bar_queue.put_nowait(Bar())

    assert robot.must_create_foobar


def test_must_create_foobar_no_foo(factory, robot):
    factory.bar_queue.put_nowait(Bar())

    assert not robot.must_create_foobar


def test_must_create_foobar_no_bar(factory, robot):
    factory.foo_queue.put_nowait(Foo())

    assert not robot.must_create_foobar


@pytest.fixture
def mock_random(mocker):
    return mocker.patch.object(foobartory.models.random, "random")


@pytest.mark.asyncio
async def test_create_foobar_success(factory, robot, mock_random, mock_sleep):
    robot._current_activity = "create_foobar"
    foo, bar = Foo(), Bar()
    factory.foo_queue.put_nowait(foo)
    factory.bar_queue.put_nowait(bar)
    mock_random.return_value = 0.5

    await robot.create_foobar()

    assert factory.foo_queue.empty()
    assert factory.bar_queue.empty()
    foobar = factory.foobar_queue.get_nowait()
    assert factory.foobar_queue.empty()
    assert isinstance(foobar, FooBar)
    assert str(foobar) == f"{foo.id} - {bar.id}"
    mock_sleep.assert_awaited_once_with(2)


@pytest.mark.asyncio
async def test_create_foobar_failure(factory, robot, mock_random, mock_sleep):
    robot._current_activity = "create_foobar"
    foo, bar = Foo(), Bar()
    factory.foo_queue.put_nowait(foo)
    factory.bar_queue.put_nowait(bar)
    mock_random.return_value = 0.7

    await robot.create_foobar()

    assert factory.foo_queue.empty()
    assert factory.foobar_queue.empty()
    bar = factory.bar_queue.get_nowait()
    assert factory.bar_queue.empty()
    assert isinstance(bar, Bar)
    mock_sleep.assert_awaited_once_with(2)


@pytest.mark.asyncio
async def test_create_foobar_not_enough_foo(factory, robot):
    robot._current_activity = "create_foobar"
    factory.bar_queue.put_nowait(Bar())

    await robot.create_foobar()

    assert factory.bar_queue.qsize() == 1


@pytest.mark.asyncio
async def test_create_foobar_not_enough_bar(factory, robot):
    robot._current_activity = "create_foobar"
    factory.foo_queue.put_nowait(Foo())

    await robot.create_foobar()

    assert factory.foo_queue.qsize() == 1


def test_must_sell_foobar(factory, robot):
    for _ in range(3):
        factory.foobar_queue.put_nowait(FooBar(Foo(), Bar()))

    assert not factory.sell_foobar_lock.locked()
    assert robot.must_sell_foobar


def test_must_sell_foobar_not_enough_foobar(factory, robot):
    for _ in range(1):
        factory.foobar_queue.put_nowait(FooBar(Foo(), Bar()))

    assert not factory.sell_foobar_lock.locked()
    assert not robot.must_sell_foobar


@pytest.mark.asyncio
async def test_must_sell_foobar_another_robot_is_already_selling(factory, robot):
    for _ in range(3):
        factory.foobar_queue.put_nowait(FooBar(Foo(), Bar()))

    async with factory.sell_foobar_lock:
        assert not robot.must_sell_foobar


@pytest.mark.asyncio
async def test_sell_foobar(factory, robot, mock_sleep):
    """Assert that the robots sell up to 5 foobars at the same time."""

    robot._current_activity = "sell_foobar"
    for _ in range(7):
        factory.foobar_queue.put_nowait(FooBar(Foo(), Bar()))

    await robot.sell_foobar()

    assert factory.account == 5
    assert factory.foobar_queue.qsize() == 2
    mock_sleep.assert_awaited_once_with(10)


def test_must_buy_robot(factory, robot):
    factory.account = 3
    for _ in range(6):
        factory.foo_queue.put_nowait(Foo())

    assert not factory.buy_robot_lock.locked()
    assert robot.must_buy_robot


def test_must_buy_robot_not_enough_cash(factory, robot):
    factory.account = 2
    for _ in range(6):
        factory.foo_queue.put_nowait(Foo())

    assert not factory.buy_robot_lock.locked()
    assert not robot.must_buy_robot


def test_must_buy_robot_not_enough_foo(factory, robot):
    factory.account = 3
    for _ in range(5):
        factory.foo_queue.put_nowait(Foo())

    assert not factory.buy_robot_lock.locked()
    assert not robot.must_buy_robot


@pytest.mark.asyncio
async def test_must_buy_robot_another_robot_is_already_buying(factory, robot):
    factory.account = 3
    for _ in range(6):
        factory.foo_queue.put_nowait(Foo())

    async with factory.buy_robot_lock:
        assert not robot.must_buy_robot


@pytest.mark.asyncio
async def test_buy_robot(factory, robot):
    robot._current_activity = "buy_robot"
    factory.account = 5
    for _ in range(8):
        factory.foo_queue.put_nowait(Foo())
    assert len(factory.robots) == 1

    await robot.buy_robot()

    assert factory.account == 2
    assert factory.foo_queue.qsize() == 2
    assert len(factory.robots) == 2


@pytest.mark.asyncio
async def test_buy_robot_not_enough_money(factory, robot):
    robot._current_activity = "buy_robot"
    factory.account = 2
    for _ in range(8):
        factory.foo_queue.put_nowait(Foo())

    await robot.buy_robot()

    assert factory.account == 2
    assert factory.foo_queue.qsize() == 8
    assert len(factory.robots) == 1


@pytest.mark.asyncio
async def test_buy_robot_not_enough_foo(factory, robot):
    robot._current_activity = "buy_robot"
    factory.account = 6
    for _ in range(2):
        factory.foo_queue.put_nowait(Foo())

    await robot.buy_robot()

    assert factory.account == 6
    assert factory.foo_queue.qsize() == 2
    assert len(factory.robots) == 1


def test_add_robot(mocker, factory):
    mock_create_task = mocker.patch.object(foobartory.models.asyncio, "create_task")
    robot = Robot(factory)
    factory.add_robot(robot)

    assert len(factory.robots) == 1
    mock_create_task.assert_called_once()
    assert mock_create_task.call_args[0][0].__name__ == "run"


@pytest.mark.asyncio
async def test_add_robot_end_the_game(factory):
    for _ in range(29):
        factory.add_robot(Robot(factory))

    assert all(not robot._stopped for robot in factory.robots)
    factory.add_robot(Robot(factory))
    assert all(robot._stopped for robot in factory.robots)


def test_factory_str(factory):
    assert str(factory) == "robots: 0,\naccount: 0,\nfoo: 0,\nbar: 0,\nfoobar: 0"
