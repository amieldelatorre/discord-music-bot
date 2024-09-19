import typing
import abc
from .mongodb_client import MongoDbClient


class KeyValueRepositoryInterface(abc.ABC):
    async def create(self, doc_id: str, values: typing.Dict):
        raise NotImplementedError

    async def get(self, doc_id: str) -> typing.Optional[typing.Dict]:
        raise NotImplementedError

    async def update(self, doc_id: str, values: typing.Dict):
        raise NotImplementedError

    async def delete(self, doc_id: str):
        raise NotImplementedError


class MongoKeyValueRepository(KeyValueRepositoryInterface):
    def __init__(self, client: MongoDbClient, collection_name: str):
        self.mongodb_client = client
        self.collection = collection_name

    async def create(self, doc_id: str, values: typing.Dict):
        doc = {
            "_id": doc_id,
            **values
        }
        return await self.mongodb_client.insert_one(self.collection, doc)

    async def get(self, doc_id: str) -> typing.Optional[typing.Dict]:
        return await self.mongodb_client.get_one(self.collection, doc_id)

    async def update(self, doc_id: str, values: typing.Dict):
        return await self.mongodb_client.update_one(self.collection, doc_id, values)

    async def delete(self, doc_id: str):
        return await self.mongodb_client.delete_one_by_id(self.collection, doc_id)

