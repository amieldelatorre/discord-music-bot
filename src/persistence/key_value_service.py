import typing
from .key_value_repository import KeyValueRepositoryInterface


class KeyValueService:
    def __init__(self, key_value_repository: KeyValueRepositoryInterface):
        self.key_value_repository = key_value_repository

    async def create(self, doc_id: str, values: typing.Dict):
        return await self.key_value_repository.create(doc_id, values)

    async def get(self, doc_id: str) -> typing.Optional[typing.Dict]:
        result = await self.key_value_repository.get(doc_id)
        if result is None:
            return None
        return result

    async def update(self, doc_id: str, values: typing.Dict):
        return await self.key_value_repository.update(doc_id, values)

    async def delete(self, doc_id: str):
        return await self.key_value_repository.delete(doc_id)

    async def set_key_overwrite_existing(self, doc_id: str, value: typing.Dict):
        result = await self.get(doc_id)
        if result is None:
            await self.create(doc_id, value)
        else:
            await self.update(doc_id, value)
