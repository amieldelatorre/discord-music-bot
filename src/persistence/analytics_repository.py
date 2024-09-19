import typing
import abc
from .opensearch_client import OpenSearchClient


class AnalyticsRepositoryInterface(abc.ABC):
    async def create(self, index: str, doc_id: str, data: typing.Dict):
        raise NotImplementedError

    async def get(self, index: str, doc_id: str) -> typing.Optional[typing.Dict]:
        raise NotImplementedError

    async def search(self, index_pattern: str, search: typing.Dict) -> typing.List[typing.Dict]:
        raise NotImplementedError

    async def update(self, index: str, doc_id: str, data: typing.Dict):
        raise NotImplementedError

    async def delete(self, index: str, doc_id: str):
        raise NotImplementedError


class OpenSearchAnalyticsRepository(AnalyticsRepositoryInterface):
    def __init__(self, client: OpenSearchClient):
        self.client = client


class DisabledAnalyticsRepository(AnalyticsRepositoryInterface):
    async def create(self, index: str, doc_id: str, data: typing.Dict):
        pass

    async def get(self, index: str, doc_id: str) -> typing.Optional[typing.Dict]:
        pass

    async def search(self, index_pattern: str, search: typing.Dict) -> typing.List[typing.Dict]:
        pass

    async def update(self, index: str, doc_id: str, data: typing.Dict):
        pass

    async def delete(self, index: str, doc_id: str):
        pass
