from typing import Union

from loguru import logger
from telethon import TelegramClient
from telethon.tl.types import Message


async def send_message_to_user(bot: TelegramClient, user: dict, message: Union[str, Message]) -> None:
    try:
        await bot.send_message(user["_id"], message)
    except Exception as e:
        logger.warning("Exception occurred {}. Unable to send message to user User {} .", e, user)
