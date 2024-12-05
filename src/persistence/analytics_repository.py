import typing
import abc
import opensearchpy
import logging
from config import logger


class AnalyticsRepositoryInterface(abc.ABC):
    async def create(self, index: str, doc_id: str, data: typing.Dict):
        raise NotImplementedError

    async def get(self, index: str, doc_id: str) -> typing.Optional[typing.Dict]:
        raise NotImplementedError

    async def search_by_field(self, index_pattern: str, field: str, query: typing.Dict) -> typing.List[typing.Dict]:
        raise NotImplementedError

    async def update(self, index: str, doc_id: str, data: typing.Dict):
        raise NotImplementedError

    async def delete(self, index: str, doc_id: str):
        raise NotImplementedError


def catch_opensearch_errors_return_none(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except opensearchpy.exceptions.NotFoundError:
            logger.log(logging.INFO, f"Opensearch not found error")
            return None
    return wrapper


def catch_opensearch_errors_return_false(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except opensearchpy.exceptions.NotFoundError:
            logger.log(logging.INFO, f"Opensearch not found error")
            return False
    return wrapper


class OpenSearchAnalyticsRepository(AnalyticsRepositoryInterface):
    def __init__(self, client: opensearchpy.AsyncOpenSearch):
        self.client = client

    @catch_opensearch_errors_return_none
    async def get(self, index: str, doc_id: str) -> typing.Optional[typing.Dict]:
        return (await self.client.get(
            index=index,
            id=doc_id
        )).get("_source")

    @catch_opensearch_errors_return_none
    async def search_by_field(self, index_pattern: str, field: str, query: typing.Dict) -> typing.List[typing.Dict]:
        raise NotImplementedError

    @catch_opensearch_errors_return_none
    async def update(self, index: str, doc_id: str, data: typing.Dict):
        raise NotImplementedError

    @catch_opensearch_errors_return_false
    async def delete(self, index: str, doc_id: str) -> bool:
        return (await self.client.delete(
            index=index,
            id=doc_id
        )).get("result") == "deleted"


class DisabledAnalyticsRepository(AnalyticsRepositoryInterface):
    async def create(self, index: str, doc_id: str, data: typing.Dict):
        pass

    async def get(self, index: str, doc_id: str) -> typing.Optional[typing.Dict]:
        pass

    async def search_by_field(self, index_pattern: str, field: str, query: typing.Dict) -> typing.List[typing.Dict]:
        pass

    async def update(self, index: str, doc_id: str, data: typing.Dict):
        pass

    async def delete(self, index: str, doc_id: str):
        pass
