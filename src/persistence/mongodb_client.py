import typing
import motor.motor_asyncio


class MongoDbClient:
    def __init__(self, host: str, port: str, database: str, username: str, password: str):
       connection_string = f"mongodb://{username}:{password}@{host}:{port}/"
       client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)

       self.database_connection = client[database]

    async def insert_one(self, collection: str, data: typing.Dict) -> str:
        result = await self.database_connection[collection].insert_one(data)
        return result.inserted_id

    async def delete_one_by_id(self, collection: str, doc_id: str) -> int:
       result = await self.database_connection[collection].delete_one({"_id": doc_id})
       return result.deleted_count

    async def get_one(self, collection: str, doc_id: str) -> typing.Dict:
        result = await self.database_connection[collection].find_one({"_id": doc_id})
        return result

    async def get_all(self, collection: str) -> typing.List[typing.Dict]:
        cursor = self.database_connection[collection].find({})

        result = []
        async for doc in cursor:
            result.append(doc)
        return result

    async def update_one(self, collection: str, doc_id: str, data: typing.Dict) -> bool:
        result = await self.database_connection[collection].replace_one({"_id": doc_id}, data)
        return result.modified_count > 1
