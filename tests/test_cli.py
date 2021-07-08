import logging
from pathlib import Path

import pytest
from click.testing import CliRunner

from foobartory import cli


@pytest.mark.parametrize(
    "verbosity, expected_level",
    [
        (0, logging.WARNING),
        (1, logging.INFO),
        (2, logging.DEBUG),
    ],
)
def test_configure_logging(mocker, caplog, verbosity, expected_level):
    config = mocker.patch("logging.basicConfig")

    caplog.set_level("DEBUG")

    cli.configure_logging(verbosity=verbosity)

    config.assert_called_once_with(level=expected_level)
    records = [record for record in caplog.records if record.action == "set_log_level"]
    assert len(records) == 1
    assert records[0].value == logging.getLevelName(expected_level)


def test_cli():
    result = CliRunner().invoke(cli.cli, [f"--speed={1e9}", "-v"])
    assert result.exit_code == 0
    banner_path = Path(__file__).parent.parent / Path("foobartory/banner.txt")
    with open(banner_path) as f:
        banner = f.read()

    assert (
        result.output
        == f"""{banner}
[*] Starting factory...
[*] You now have 3 robots
[*] You now have 4 robots
[*] You now have 5 robots
[*] You now have 6 robots
[*] You now have 7 robots
[*] You now have 8 robots
[*] You now have 9 robots
[*] You now have 10 robots
[*] You now have 11 robots
[*] You now have 12 robots
[*] You now have 13 robots
[*] You now have 14 robots
[*] You now have 15 robots
[*] You now have 16 robots
[*] You now have 17 robots
[*] You now have 18 robots
[*] You now have 19 robots
[*] You now have 20 robots
[*] You now have 21 robots
[*] You now have 22 robots
[*] You now have 23 robots
[*] You now have 24 robots
[*] You now have 25 robots
[*] You now have 26 robots
[*] You now have 27 robots
[*] You now have 28 robots
[*] You now have 29 robots
[+] Congratulation, you have 30 robots!
"""
    )


def test_main(mocker):
    # This is just to reach 100% coverage
    mock = mocker.patch.object(cli, "cli")
    cli.main()
    assert mock.called is True
