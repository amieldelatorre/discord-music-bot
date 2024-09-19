import persistence
from .default_bot import default_bot, get_default_bot_config
from .music_bot import MusicBot, get_music_bot_config
from config import get_required_environment_variable, get_environment_variable_with_default, logger, set_log_level
from dotenv import load_dotenv


async def main():
    load_dotenv()
    global_config = get_default_bot_config()
    musicbot_config = get_music_bot_config()
    set_log_level(global_config.log_level)

    mongo_client = persistence.mongodb_client.MongoDbClient(
        host=musicbot_config.mongodb_host,
        port=musicbot_config.mongodb_port,
        database=musicbot_config.mongodb_database,
        username=musicbot_config.mongodb_username,
        password=musicbot_config.mongodb_password
    )

    queue_repo = persistence.queue_repository.MongoDbQueueRepository(mongo_client, "music_queues")
    queue_service = persistence.queue_service.QueueService(
        queue_repository=queue_repo
    )

    key_value_repo = persistence.key_value_repository.MongoKeyValueRepository(mongo_client, "now_playing")
    key_value_service = persistence.key_value_service.KeyValueService(
        key_value_repository=key_value_repo
    )

    await default_bot.add_cog(MusicBot(default_bot, musicbot_config, queue_service, key_value_service))
    await default_bot.start(global_config.discord_token)
