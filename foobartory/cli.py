import asyncio
import logging
from pathlib import Path

import click

from foobartory.models import Factory, Robot

logger = logging.getLogger(__name__)


def configure_logging(verbosity: int) -> None:
    """Given the number of repetitions of the flag -v, set the desired log level."""

    level = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}.get(verbosity, 0)
    logging.basicConfig(level=level)
    level_name = logging.getLevelName(level)
    logger.debug(
        f"Log level set to {level_name}",
        extra={"action": "set_log_level", "value": level_name},
    )


@click.command(name="foobartory")
@click.option(
    "-s",
    "--speed",
    default=1,
    type=float,
    help="Fasten the factory by the given factory (1 by default)",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Use multiple times to increase verbosity",
)
def cli(speed: float, verbose: int) -> None:
    configure_logging(verbose)

    banner_path = Path(__file__).parent / Path("banner.txt")
    with open(banner_path) as f:
        click.echo(f.read())

    factory = Factory(speed=speed)

    # Append the robots separately so they both have a distinct id
    factory.robots.append(Robot(factory=factory))
    factory.robots.append(Robot(factory=factory))

    tasks = [robot.run() for robot in factory.robots]
    click.echo("[*] Starting factory...")
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))


def main():
    return cli()
