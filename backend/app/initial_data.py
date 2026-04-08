import logging

from sqlmodel import Session

from app.core.db import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with Session(engine) as session:
        results = init_db(session)
    logger.info(
        "Seeded role users: admin=%s manager=%s member=%s",
        results["admin"],
        results["manager"],
        results["member"],
    )


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
