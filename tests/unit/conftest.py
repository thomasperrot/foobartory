import pytest

from foobartory import models


@pytest.fixture
def factory():
    return models.Factory()


@pytest.fixture(autouse=True)
def mock_sleep(mocker):
    return mocker.patch.object(models.asyncio, "sleep")
