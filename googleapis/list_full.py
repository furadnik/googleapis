"""An utility module for listing all items via next page tokens."""
from typing import Callable, Iterator, TypeVar

T = TypeVar("T")


def list_all(func: Callable, *args, **kwargs) -> Iterator[T]:
    """List all via next page token."""
    next_page_token = None
    while True:
        data = func(*args, **kwargs, pageToken=next_page_token).execute()
        next_page_token = data.get("nextPageToken", None)
        yield from data["items"]
        if next_page_token is None:
            break
