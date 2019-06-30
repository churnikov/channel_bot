import asyncio
import logging
import logging.config as logging_config
import sqlite3
from typing import Tuple, Union

from dependencies import Injector
from telethon import TelegramClient, events
from telethon.events import NewMessage
from telethon.tl.types import User

from config import *
from extractor import FetchNewTelegramPosts
from loader import UserContainer, TelegramResourcesContainer

logging_config.fileConfig("logger.config")
logger = logging.getLogger(__name__)

bot = TelegramClient("bot", API_ID, API_HASH)
bot.start(bot_token=BOT_TOKEN)
client = TelegramClient("anon", API_ID, API_HASH)
client.start()


class PostsContainer(Injector):
    fetch = FetchNewTelegramPosts
    db = TelegramResourcesContainer
    tg_client = client


async def run():
    while True:
        try:
            new_posts = await PostsContainer.fetch()
            for user in UserContainer.iterate():
                user_channels = user["subscriptions"]
                for uc in user_channels:
                    posts = new_posts.get(uc)
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
            "Use /sub vk <group_name> to subscribe to vk group\n"
            "Use /unsub channel_name to unsubscribe from channel\n"
            "Use /list to list channels you are subscribed to"
        )
    else:
        await event.respond(
            "Hello again!\n"
            "Use /sub telegram https://t.me/channel_name/79 to subscribe to telegram channel\n"
            "Use /sub vk <group_name> to subscribe to vk group\n"
            "Use /unsub channel_name to unsubscribe from channel\n"
            "Use /list to list channels you are subscribed to"
        )


def parse_post_url(post_url) -> Union[Tuple[str, int], Tuple[None, None]]:
    try:
        channel_name, post_id_str = post_url.split("/")[-2:]
        post_id = int(post_id_str)
        return channel_name, post_id
    except ValueError:
        logger.info("Could not process %s", post_url)
        return None, None


@bot.on(events.NewMessage(pattern="/sub"))
async def subscribe(event: NewMessage.Event):
    user: User = event.message.sender
    resource_name, post_url = event.message.text.split()[-2:]

    if resource_name == "telegram":
        channel_name, post_id = parse_post_url(post_url)

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
                logger.warning("User %d supplied wrong entity, %s", user.id, str(e))
    elif resource_name == "vk":
        # TODO
        message = "VK is not supported right now"

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
            channel_id = (await client.get_input_entity(channel_name)).channel_id
            UserContainer.unsubscribe(user.id, channel_id, resource_name)
            message = f"You have unsubscribed from {channel_name}"
        except Exception as e:
            message = (
                "What you have supplied is not a channel\n"
                "Command should be /unsub <resource_name> <channel_name>"
            )
            logger.warning("User %d supplied wrong entity, %s", user.id, str(e))

    await event.respond(message)


@bot.on(events.NewMessage(pattern="/list"))
async def list_channels(event: NewMessage.Event):
    user: User = event.message.sender
    channel_ids = UserContainer.list_subscriptions(user.id)
    channels = TelegramResourcesContainer.get_resources_names(channel_ids)
    await event.respond(str(channels))


loop = asyncio.get_event_loop()
loop.create_task(run())

bot.run_until_disconnected()
