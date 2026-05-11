import logging

from src.config import config
from src.services.worker import SmartWaterWorker


def main():
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    worker = SmartWaterWorker()
    worker.start()


if __name__ == "__main__":
    main()
