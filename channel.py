import logging
import sqlite3
from time import sleep
from typing import Dict, List

from dependencies import Injector
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetMessagesRequest
from telethon.tl.types import MessageEmpty

from config import *
from database import ResourcesContainer, UserContainer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler("channels_bot.log")
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)


class FetchNewPosts:
    def __init__(self, db: ResourcesContainer, tg_client: TelegramClient):
        self.db = db
        self.tg_client = tg_client

    def generate_post_url(self, channel_id: int, posts_ids):
        channel_name = self.db.get_resources_names([channel_id])[0]
        return [f"https://t.me/{channel_name}/{pid}" for pid in posts_ids]

    def get_new_channel_posts(self, channel_id: int, recent_id: int):

        ids_to_check = list(range(recent_id, recent_id + 10))

        with self.tg_client as client:
            new_posts = client(GetMessagesRequest(channel_id, ids_to_check))

        new_posts = [p.id for p in new_posts.messages if not isinstance(p, MessageEmpty)]

        if new_posts:
            recent_id = new_posts[-1] + 1
            new_posts = self.generate_post_url(channel_id, new_posts)

        return new_posts, recent_id

    def __call__(self) -> Dict[str, List[str]]:
        all_new_posts = dict()
        n_new_posts: int = 0
        for channel in self.db.iterate():
            recent_id = channel["recent_post_id"]
            channel_id = channel["_id"]

            new_posts, recent_id = self.get_new_channel_posts(channel_id, recent_id)

            if new_posts:
                self.db.update_recent_id(channel_id, recent_id)

                all_new_posts[channel_id] = new_posts

            logger.debug("Got %d new posts from %s", len(new_posts), channel_id)
            n_new_posts += len(new_posts)

        logger.info("Got %d new posts", n_new_posts)

        return all_new_posts


class PostsContainer(Injector):
    fetch = FetchNewPosts
    db = ResourcesContainer
    tg_client = TelegramClient(session="anon", api_id=API_ID, api_hash=API_HASH)


if __name__ == "__main__":
    bot = TelegramClient("sender", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    while True:
        try:
            new_posts = PostsContainer.fetch()
            for user in UserContainer.iterate():
                user_channels = user["subscriptions"]
                for uc in user_channels:
                    posts = new_posts.get(uc)
                    if posts:
                        for post in posts:
                            bot.send_message(user["_id"], post)

            sleep(15)
        except sqlite3.OperationalError as e:
            logger.warning(e)
            continue
