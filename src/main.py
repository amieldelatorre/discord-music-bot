# import opensearchpy

#
# host = "localhost"
# port = "9200"
# auth = ('admin', 'Pasdfghjkl!12')
#
# client = opensearchpy.OpenSearch(
#     hosts=[{'host': host, 'port': port}],
#     http_compress=True,
#     http_auth=auth,
#     use_ssl=True,
#     verify_certs=False,
#     ssl_assert_hostname=False,
#     ssl_show_warn=False
# )
#
# doc = {
#     'title': "test",
#     'value': "something"
# }
#
# response = client.index(
#     index="testme",
#     body=doc,
#     refresh=True
# )
#
# print(response)

import persistence.mongodb_client
import persistence.queue_service
import persistence.queue_repository


async def main():
    host = "localhost"
    port = "27017"
    username = "root"
    password = "password"
    database = "discord_bot"

    mongo_client = persistence.mongodb_client.MongoDbClient(
        host=host,
        port=port,
        database=database,
        username=username,
        password=password
    )

    queue_repo = persistence.queue_repository.MongoDbQueueRepository(mongo_client, "music_queues")

    queue_service = persistence.queue_service.QueueService(
        queue_repository=queue_repo
    )

    # item = {
    #     "_id": "123455",
    #     "value": "123455566"
    # }
    #
    # print(await mongo_client.insert_one(
    #     collection="music_queues",
    #     data=item))
    #
    # res = await mongo_client.get_one(
    #     collection="music_queues",
    #     id=item["_id"]
    # )
    #
    # print(res, type(res))

    # print(await mongo_client.delete_one_by_id(
    #     collection="music_queues",
    #     id=item["_id"]
    # ))

    # data = {
    #     "_id": "1234567890",
    #     "items": [
    #         {
    #             "id": "123456"
    #         }
    #     ]
    # }
    # await queue_service.add_queue(data)
    #
    # print(await queue_service.get_all_queues())
    #
    # await queue_service.append_to_queue(data["_id"], {"id": "09876"})
    # print(await queue_service.get_all_queues())
    # print(await queue_service.get_queue_size(doc_id="_id"))
    # print(await queue_service.is_queue_empty(doc_id="1234567890"))
    # print(await queue_service.is_queue_index_valid(doc_id="1234567890", index=0))
    # print(await queue_service.queue_index_pop(doc_id="1234567890", index=2))
    # print(await queue_service.get_queue_by_id(doc_id="1234567890"))

import asyncio
import bot
import yt
asyncio.run(bot.main())
