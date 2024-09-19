import typing
import opensearchpy


class OpenSearchClient:
    def __init__(self, host: str, port: int, username: str, password: str,
                 verify_certs: bool = False, ssl_assert_hostname: bool = False, ssl_show_warn: bool = False):
        client = opensearchpy.AsyncOpenSearch(
            hosts=[
                {
                    "host": host,
                    "port": port
                }
            ],
            http_compress=True,
            http_auth=(username, password),
            use_ssl=True,
            verify_certs=verify_certs,
            ssl_assert_hostname=ssl_assert_hostname,
            ssl_show_warn=ssl_show_warn
        )

        self.client = client

    async def create(self, index: str, data: typing.Dict, doc_id: str = None) -> str:
        result = await self.client.index(
            index=index,
            body=data,
            id=doc_id
        )

        return result.get("_id")

    # TODO: paging
    async def simple_search(self, index: str, field: str, query: typing.Dict, operator: str, size: int = 100) -> typing.Dict:
        q = {
            "size": size,
            "query": {
                "match": {
                    field: query,
                }
            }
        }

        results = await self.client.search(
            body=q,
            index=index
        )

        found = {
            "total": results.get("hits").get("total").get("value"),
            "items": results.get("hits").get("hits")
        }

        return found

    async def get(self, index: str, doc_id: str) -> typing.Optional[typing.Dict]:
        try:
            return await self.client.get(
                index=index,
                id=doc_id
            )
        except opensearchpy.exceptions.NotFoundError:
            return None

    async def delete(self, index: str, doc_id: str) -> bool:
        try:
            result = await self.client.delete(
                index=index,
                id=doc_id
            )

            return result.get("result") == "deleted"
        except opensearchpy.exceptions.NotFoundError:
            return False



