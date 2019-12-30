import asyncio

import pytest
from mongomock import Collection, MongoClient
from telethon import TelegramClient

from channel_bot.db_query import TelegramResourcesContainer, UserContainer
from channel_bot.remote_fetcher import FetchNewTelegramPosts
from config import TG_API_HASH, TG_API_ID


@pytest.fixture()
def tg_client():
    with TelegramClient("anon", TG_API_ID, TG_API_HASH) as client:
        client.start()
        yield client


@pytest.fixture()
def mongo_client():
    mc = MongoClient()
    col: Collection = mc.channels_bot.telegram_resources
    col.insert_many([{"_id": 1067810422, "name": "popyachsa", "recent_post_id": 39582}])
    yield mc
    mc.drop_database("channels_bot")


def test_tg_fetch(tg_client: TelegramClient, mongo_client):
    trc = TelegramResourcesContainer.let(mc=mongo_client)
    fetch = FetchNewTelegramPosts(db=trc, tg_client=tg_client)
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(fetch())
    print(res)
    assert len(res) > 0


def test_tg_subscribe(tg_client: TelegramClient, mongo_client):
    uc = UserContainer.let(mc=mongo_client)
    trc = TelegramResourcesContainer.let(mc=mongo_client)

    channel_id = tg_client.get_input_entity("popyachsa").channel_id
    uc.subscribe(1, channel_id, "telegram")
    trc.add_new_resource("popyachsa", channel_id, 28530)
