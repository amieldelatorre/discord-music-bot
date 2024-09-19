import typing
from dataclasses import dataclass


@dataclass
class Song:
    filename: str
    title: str
    url: str
    author: str


@dataclass
class Queue:
    queue_id: str
    items: typing.List[typing.Any]

    def append(self, item: typing.Any):
        if self.items is None:
            self.items = [item]
            return

        self.items.append(item)
        return

    def size(self) -> int:
        return len(self.items)

    def is_empty(self) -> bool:
        return self.items is None or len(self.items) <= 0

    def is_0_base_index_valid(self, index: int) -> bool:
        queue_size = self.size()
        return 0 <= index < queue_size

    def is_1_base_index_valid(self, index: int) -> bool:
        queue_size = size = self.size()
        return 1 <= index <= queue_size

    def pop_index(self, index: int) -> typing.Any:
        item = self.items.pop(index)
        return item
