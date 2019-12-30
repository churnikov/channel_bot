import asyncio
import pprint
import sqlite3
from typing import Dict, List, Tuple, Union

from dependencies import Injector
from loguru import logger
from telethon import TelegramClient, events
from telethon.events import NewMessage
from telethon.tl.types import User

from channel_bot.db_query import TelegramResourcesContainer, UserContainer
from channel_bot.remote_fetcher import FetchNewTelegramPosts
from config import *

bot = TelegramClient("bot", TG_API_ID, TG_API_HASH)
bot.start(bot_token=TG_BOT_TOKEN)
client = TelegramClient("anon", TG_API_ID, TG_API_HASH)
client.start()


class WrongResourceTypeException(Exception):
    pass


class TelegramPostsContainer(Injector):
    fetch = FetchNewTelegramPosts
    db = TelegramResourcesContainer
    tg_client = client


async def run():
    while True:
        try:
            new_posts = {"telegram": await TelegramPostsContainer.fetch()}
            for user in UserContainer.iterate():
                for user_resource, user_channels in user["resources"].items():
                    if user_channels:
                        for uc in user_channels:
                            posts = new_posts[user_resource].get(uc)
                            if posts:
                                for post in posts:
                                    await bot.send_message(user["_id"], post)

            await asyncio.sleep(15)
        except sqlite3.OperationalError as e:
            logger.warning(e)
            continue


@bot.on(events.NewMessage(pattern="/start"))
async def start(event: NewMessage.Event):
    user: User = event.message.sender
    is_new = UserContainer.add_new_user(user.id)
    if is_new:
        await event.respond(
            "Hello! I'm not yet another channels bot \n"
            "Use /sub telegram https://t.me/channel_name/79 to subscribe to telegram channel\n"
            "Use /unsub <resource_name> <channel_name> to unsubscribe from channel\n"
            "Use /list to list channels you are subscribed to"
        )
    else:
        await event.respond(
            "Hello again!\n"
            "Use /sub telegram https://t.me/channel_name/79 to subscribe to telegram channel\n"
            "Use /unsub <resource_name> <channel_name> to unsubscribe from channel\n"
            "Use /list to list channels you are subscribed to"
        )


def parse_post_url(post_url) -> Union[Tuple[str, int], Tuple[None, None]]:
    try:
        channel_name, post_id_str = post_url.split("/")[-2:]
        post_id = int(post_id_str)
        return channel_name, post_id
    except ValueError:
        logger.info("Could not process {}", post_url)
        return None, None


async def channel_name2id(channel_name: str, resource_name: str) -> int:
    if resource_name == "telegram":
        channel_id: int = (await client.get_input_entity(channel_name)).channel_id
    else:
        raise WrongResourceTypeException

    return channel_id


@bot.on(events.NewMessage(pattern="/sub"))
async def subscribe(event: NewMessage.Event):
    """
    Subscribe user to remote resource.
    
    This handler expects 2 arguments: resource name (currently only telegram) and link to post from this resource.
    
    If resource is not supported, we will return message that we don't support this type of resource.
    
    :param event: 
    :return: 
    """
    user: User = event.message.sender
    resource_name, channel_info = event.message.text.split()[-2:]

    if resource_name == "telegram":
        channel_name, post_id = parse_post_url(channel_info)

        if channel_name is None:
            message = (
                f"Url you supplied was wrong, it should be like https://t.me/channel_name/79",
            )
        else:
            try:
                channel_id = (await client.get_input_entity(channel_name)).channel_id
                UserContainer.subscribe(user.id, channel_id, "telegram")
                TelegramResourcesContainer.add_new_resource(channel_name, channel_id, post_id)
                message = f"You have subscribed to {channel_name}"
            except Exception as e:
                message = "What you have supplied is not a channel"
                logger.warning("User {} supplied wrong entity, {}", user.id, str(e))
    else:
        message = f"{resource_name} is not supported"

    await event.respond(message)


@bot.on(events.NewMessage(pattern="/unsub"))
async def unsubscribe(event: NewMessage.Event):
    user: User = event.message.sender
    query = event.message.text.split()

    if len(query) == 1:
        message = (
            "You did not provide channel name to unsubscribe.\n"
            "Command should be /unsub <resource_name> <channel_name>"
        )
    else:
        try:
            resource_name, channel_name = query[1], query[2]
            message = f"You have unsubscribed from {channel_name}"
            if resource_name in ("vk", "telegram"):
                channel_id = await channel_name2id(channel_name, resource_name)
                UserContainer.unsubscribe(user.id, channel_id, resource_name)
            else:
                message = "Please type resource name as 'vk' or 'telegram'"

        except Exception as e:
            message = (
                "What you have supplied is not a channel\n"
                "Command should be /unsub <resource_name> <channel_name>"
            )
            logger.warning("User {} supplied wrong entity, {}", user.id, str(e))

    await event.respond(message)


@bot.on(events.NewMessage(pattern="/list"))
async def list_channels(event: NewMessage.Event):
    user: User = event.message.sender
    resources: Dict[str, List[str]] = UserContainer.list_subscriptions(user.id)
    result = {
        "telegram": TelegramResourcesContainer.get_resources_names(resources.get("telegram", []))
    }
    await event.respond(pprint.pformat(result))


loop = asyncio.get_event_loop()
loop.create_task(run())

bot.run_until_disconnected()
