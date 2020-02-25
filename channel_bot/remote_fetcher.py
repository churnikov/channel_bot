from typing import Dict, List

from loguru import logger
from telethon.sync import TelegramClient
from telethon.tl.types import MessageEmpty

from channel_bot.db_query import TelegramResourcesContainer


class FetchNewTelegramPosts:
    def __init__(self, db: TelegramResourcesContainer, tg_client: TelegramClient):
        self.db = db
        self.tg_client = tg_client

    def generate_post_url(self, channel_id: int, posts_ids):
        channel_name = self.db.get_resources_names([channel_id])[0]
        return [f"https://t.me/{channel_name}/{pid}" for pid in posts_ids]

    async def get_new_channel_posts(self, channel_id: int, recent_id: int):

        try:
            new_posts = self.tg_client.iter_messages(channel_id, min_id=recent_id, limit=10)

            new_posts = [p.id async for p in new_posts if not isinstance(p, MessageEmpty)]

            if new_posts:
                recent_id = max(new_posts) + 1
                new_posts = self.generate_post_url(channel_id, new_posts)

            return new_posts, recent_id
        except ValueError:
            logger.exception("Could not process {}", channel_id)
            return [], recent_id

    async def __call__(self) -> Dict[str, List[str]]:
        all_new_posts = dict()
        n_new_posts: int = 0
        for channel in self.db.iterate():
            recent_id = channel["recent_post_id"]
            channel_id = channel["_id"]

            new_posts, recent_id = await self.get_new_channel_posts(channel_id, recent_id)

            if new_posts:
                self.db.update_recent_id(channel_id, recent_id)

                all_new_posts[channel_id] = new_posts

            logger.debug("Got {} new posts from {}", len(new_posts), channel_id)
            n_new_posts += len(new_posts)

        logger.info("Got {} new posts", n_new_posts)

        return all_new_posts
