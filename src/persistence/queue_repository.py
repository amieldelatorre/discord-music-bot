import typing
import abc
from .mongodb_client import MongoDbClient


class QueueRepositoryInterface(abc.ABC):
    async def add_queue(self, doc_id: str, data: typing.List) -> str:
        raise NotImplementedError()

    async def delete_queue_by_id(self, doc_id: str) -> int:
        raise NotImplementedError()

    async def get_queue_by_id(self, doc_id: str) -> typing.Dict:
        raise NotImplementedError

    async def get_all_queues(self) -> typing.List[typing.Dict]:
        raise NotImplementedError

    async def update_queue_by_id(self, doc_id: str, data: typing.Dict) -> bool:
        raise NotImplementedError


class MongoDbQueueRepository(QueueRepositoryInterface):
    def __init__(self, client: MongoDbClient, collection_name: str):
        self.mongodb_client = client
        self.collection = collection_name

    async def add_queue(self, doc_id: str, queue: typing.List) -> str:
        doc = {
            "_id": doc_id,
            "items": queue
        }
        result = await self.mongodb_client.insert_one(self.collection, doc)
        return result

    async def delete_queue_by_id(self, doc_id: str) -> int:
       result = await self.mongodb_client.delete_one_by_id(self.collection, doc_id)
       return result

    async def get_queue_by_id(self, doc_id: str) -> typing.Dict:
        result = await self.mongodb_client.get_one(self.collection, doc_id)
        return result

    async def get_all_queues(self) -> typing.List[typing.Dict]:
        result = await self.mongodb_client.get_all(self.collection)
        return result

    async def update_queue_by_id(self, doc_id: str, data: typing.Dict) -> bool:
        result = await self.mongodb_client.update_one(self.collection, doc_id, data)
        return result
