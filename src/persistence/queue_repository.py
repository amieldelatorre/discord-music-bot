import typing
import abc
import motor.motor_asyncio

import models


class QueueRepositoryInterface(abc.ABC):
    async def add_queue(self, queue: models.Queue) -> str:
        raise NotImplementedError()

    async def delete_queue_by_id(self, queue_id: str) -> int:
        raise NotImplementedError()

    async def get_queue_by_id(self, queue_id: str) -> typing.Dict:
        raise NotImplementedError

    async def get_all_queues(self) -> typing.List[typing.Dict]:
        raise NotImplementedError

    async def update_queue(self, queue: models.Queue) -> bool:
        raise NotImplementedError


class MongoDbQueueRepository(QueueRepositoryInterface):
    def __init__(self, host: str, port: str, database: str, username: str, password: str, collection_name: str):
        connection_string = f"mongodb://{username}:{password}@{host}:{port}/"
        client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
        self.mongodb_client = client
        self.collection = collection_name

    async def add_queue(self, queue: models.Queue) -> str:
        doc = {
            "_id": queue.queue_id,
            "items": queue.items_to_dict()
        }
        result = await self.mongodb_client[self.collection].insert_one(doc)
        return result.inserted_id

    async def delete_queue_by_id(self, queue_id: str) -> int:
        doc = {
            "_id": queue_id
        }
        result = await self.mongodb_client[self.collection].delete_one(doc)
        return result.deleted_count

    async def get_queue_by_id(self, queue_id: str) -> typing.Dict:
        doc = {
            "_id": queue_id
        }
        result = await self.mongodb_client[self.collection].find_one(doc)
        return result

    async def get_all_queues(self) -> typing.List[typing.Dict]:
        cursor = self.mongodb_client[self.collection].find({})

        result = []
        async for doc in cursor:
            result.append(doc)
        return result

    async def update_queue(self, queue: models.Queue) -> bool:
        data = {
            "items": queue.items_to_dict()
        }
        result = await self.mongodb_client[self.collection].replace_one({"_id": queue.queue_id}, data)
        return result.modified_count > 1
