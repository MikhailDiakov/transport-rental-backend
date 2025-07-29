from time import sleep

from app.core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

engine = create_engine(settings.DB_URL_SYNC)


def wait_for_db():
    while True:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except OperationalError:
            sleep(1)


if __name__ == "__main__":
    wait_for_db()
