import logging
import discord
from dataclasses import dataclass
from discord.ext import commands
from config import get_required_environment_variable, get_environment_variable_with_default, logger, set_log_level


@dataclass
class DefaultBotConfig:
    discord_token: str
    log_level: str


def get_default_bot_config() -> DefaultBotConfig:
    discord_token = get_required_environment_variable("DISCORD_TOKEN")
    log_level = get_environment_variable_with_default("LOG_LEVEL", "INFO")
    return DefaultBotConfig(
        discord_token=discord_token,
        log_level=log_level,
    )


intents = discord.Intents.default()
intents.message_content = True
default_bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("^"),
    description="Relatively simple music default_bot",
    intents=intents
)


@default_bot.event
async def on_ready():
    logger.log(logging.INFO, f"[start] Logged in as {default_bot.user}. (ID: {default_bot.user.id})")
