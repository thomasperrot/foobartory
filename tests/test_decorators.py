import pytest

from foobartory.config import SWITCH_ACTIVITY_DELAY
from foobartory.decorators import activity
from foobartory.models import Robot


class DummyRobot(Robot):
    def __init__(self, factory) -> None:
        super().__init__(factory)
        self._current_activity = "activity_1"

    @activity
    async def activity_1(self) -> None:
        pass

    @activity
    async def activity_2(self) -> None:
        pass


@pytest.fixture
def dummy_robot(factory):
    return DummyRobot(factory)


@pytest.mark.asyncio
async def test_activity_no_change(dummy_robot, mock_sleep):
    await dummy_robot.activity_1()

    mock_sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_activity_change(dummy_robot, mock_sleep):
    await dummy_robot.activity_2()

    mock_sleep.assert_awaited_once_with(SWITCH_ACTIVITY_DELAY)
