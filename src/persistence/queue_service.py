import typing
from .queue_repository import QueueRepositoryInterface
from models import Queue


class QueueService:
    def __init__(self, queue_repository: QueueRepositoryInterface):
        self.queue_repository = queue_repository

    async def create_or_update(self, queue: Queue):
        found_queue = await self.get_queue_by_id(queue.queue_id)

        if found_queue is None:
            return await self.queue_repository.add_queue(queue.queue_id, queue.items)
        else:
            doc = {"items": queue.items}
            return await self.queue_repository.update_queue_by_id(queue.queue_id, doc)

    async def get(self, queue_id: str) -> typing.List:
        queue: typing.Dict = await self.queue_repository.get_queue_by_id(queue_id)
        if queue is None:
            return []
        return queue.get("items")

    async def delete(self, queue_id: str):
        return await self.queue_repository.delete_queue_by_id(queue_id)

    async def add_to_queue(self, doc_id: str, item: typing.Dict):
        queue = await self.get_queue_by_id(doc_id)
        if queue is None:
            return await self.queue_repository.add_queue(doc_id, [item])
        else:
            queue.append(item)
            doc = {
                "items": queue
            }
            return await self.queue_repository.update_queue_by_id(doc_id, doc)

    async def get_all_queues(self) -> typing.List[typing.Dict]:
        return await self.queue_repository.get_all_queues()

    async def get_queue_by_id(self, doc_id: str) -> typing.Optional[typing.List]:
        queue = await self.queue_repository.get_queue_by_id(doc_id)
        if queue is None:
            return None
        return queue["items"]

    async def delete_queue_by_id(self, doc_id: str):
        return await self.queue_repository.delete_queue_by_id(doc_id)

    async def get_queue_size(self, doc_id: str) -> typing.Optional[int]:
        queue = await self.get_queue_by_id(doc_id)
        if queue:
            return len(queue)
        return None

    async def is_queue_empty(self, doc_id: str) -> bool:
        queue = await self.get_queue_by_id(doc_id)
        return queue is None or len(queue) <= 0

    async def is_0_base_index_valid(self, doc_id: str, index: int) -> bool:
        queue_size = await self.get_queue_size(doc_id)
        return 0 <= index < queue_size

    async def is_1_base_index_valid(self, doc_id: str, index) -> bool:
        queue_size = await self.get_queue_size(doc_id)
        return 1 <= index <= queue_size

    async def is_queue_index_valid(self, doc_id: str, index: int) -> bool:
        queue_size = await self.get_queue_size(doc_id)
        if queue_size is None:
            raise Exception("Unexpected None")

        return 1 <= index <= queue_size

    async def queue_index_pop(self, doc_id: str, index: int):
        if await self.is_queue_empty(doc_id) or not await self.is_0_base_index_valid(doc_id, index):
            return None

        queue = await self.get_queue_by_id(doc_id)
        item = queue.pop(index)

        await self.queue_repository.update_queue_by_id(doc_id, {"items": queue})
        return item

    async def is_field_item_in_any_queue(self, field: str, value: str) -> bool:
        queues = await self.get_all_queues()

        for queue in queues:
            for item in queue.get("items"):
                if item.get(field) == value:
                    return True
        return False

    async def queue_swap_items(self, doc_id: str, index1, index2) -> bool:
        queue_items = await self.get_queue_by_id(doc_id)
        if (queue_items is None or not await self.is_0_base_index_valid(doc_id, index1) or
                not await self.is_0_base_index_valid(doc_id, index2)):
            return False

        temp = queue_items[index1]
        queue_items[index1] = queue_items[index2]
        queue_items[index2] = temp
        queue: Queue = Queue(
            queue_id=doc_id,
            items=queue_items
        )
        await self.create_or_update(queue)

        return True

    async def queue_jump(self, doc_id, index) -> typing.List[typing.Any]:
        """Jumps to a position in queue, returning the removed items"""
        queue_items = await self.get_queue_by_id(doc_id)
        if queue_items is None or not await self.is_0_base_index_valid(doc_id, index):
            return []

        items_removed = queue_items[:index]
        queue: Queue = Queue(
            queue_id=doc_id,
            items=queue_items[index:]
        )
        await self.create_or_update(queue)
        return items_removed

    async def queue_move(self, doc_id, index1, index2) -> bool:
        queue_items = await self.get_queue_by_id(doc_id)
        if (queue_items is None or not await self.is_0_base_index_valid(doc_id, index1)
                or not await self.is_0_base_index_valid(doc_id, index2)):
            return False

        item = queue_items.pop(index1)
        queue_items.insert(index2, item)
        queue: Queue = Queue(
            queue_id=doc_id,
            items=queue_items
        )
        await self.create_or_update(queue)
        return True
