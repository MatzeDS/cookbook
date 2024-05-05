from datetime import datetime, timezone
from typing import Callable, List, TypeVar


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


T = TypeVar("T")


def find(items: List[T], condition: Callable[[T], bool]) -> T | None:
    for item in items:
        if condition(item):
            return item

    return None
