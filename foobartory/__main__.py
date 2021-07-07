import asyncio
import logging

from foobartory.models import Factory, Robot


def main() -> None:
    factory = Factory()
    factory.robots.append(Robot(factory=factory))
    factory.robots.append(Robot(factory=factory))

    tasks = [robot.run() for robot in factory.robots]
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
