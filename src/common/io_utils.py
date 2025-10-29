import os
import time
import pathlib
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

DEF_USER_AGENT = (
    os.getenv("USER_AGENT")
    or "IO-Listings-POC/0.1 (+local; educational; contact@example.com)"
)


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def ensure_dir(path: str | pathlib.Path) -> pathlib.Path:
    p = pathlib.Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def polite_sleep(seconds: float) -> None:
    time.sleep(seconds)