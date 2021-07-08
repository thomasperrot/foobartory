import pytest


@pytest.mark.asyncio
async def test_switch_activity_no_change(robot, mock_sleep):
    await robot.check_activity("harvest_foo")

    assert robot._current_activity == "harvest_foo"
    mock_sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_switch_activity(robot, mock_sleep):
    await robot.check_activity("harvest_bar")

    assert robot._current_activity == "harvest_bar"
    mock_sleep.assert_awaited_once_with(5)
