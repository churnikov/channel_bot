from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetMessagesRequest
from telethon.tl.types import MessageEmpty
from typing import Dict, List, Tuple
from vk_api import VkApi

from query import TelegramResourcesContainer, VKResourcesContainer

logger = logging.getLogger(__name__)


class FetchNewTelegramPosts:
    def __init__(self, db: TelegramResourcesContainer, tg_client: TelegramClient):
        self.db = db
        self.tg_client = tg_client

    def generate_post_url(self, channel_id: int, posts_ids):
        channel_name = self.db.get_resources_names([channel_id])[0]
        return [f"https://t.me/{channel_name}/{pid}" for pid in posts_ids]

    async def get_new_channel_posts(self, channel_id: int, recent_id: int):

        try:
            ids_to_check = list(range(recent_id, recent_id + 10))

            new_posts = await self.tg_client(GetMessagesRequest(channel_id, ids_to_check))

            new_posts = [p.id for p in new_posts.messages if not isinstance(p, MessageEmpty)]

            if new_posts:
                recent_id = new_posts[-1] + 1
                new_posts = self.generate_post_url(channel_id, new_posts)

            return new_posts, recent_id
        except ValueError:
            logger.warning("Could not process %d", channel_id)
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

            logger.debug("Got %d new posts from %s", len(new_posts), channel_id)
            n_new_posts += len(new_posts)

        logger.info("Got %d new posts", n_new_posts)

        return all_new_posts


class FetchNewVKPosts:
    def __init__(self, db: VKResourcesContainer, vk_api: VkApi):
        self.vk_api = vk_api
        self.db = db

    def generate_post_url(self, channel_id: int, posts_ids: List[int]) -> List[str]:
        return [f"https://vk.com/wall-{channel_id}_{pid}" for pid in posts_ids]

    async def get_new_channel_posts(self, channel_id: int, recent_id: int) -> Tuple[List[str], int]:

        try:

            data: dict = self.vk_api.method("wall.get", {"owner_id": f"-{channel_id}", "count": 20})
            data = data["items"]
            new_posts = [p for p in data if p["id"] > recent_id and p.get("is_pinned") is None]
            recent_id: int = new_posts[0]["id"] if len(new_posts) else recent_id
            new_posts_urls = self.generate_post_url(channel_id, [p["id"] for p in new_posts])

            return new_posts_urls, recent_id
        except ValueError:
            logger.warning("Could not process %d", channel_id)
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

            logger.debug("Got %d new posts from %s", len(new_posts), channel_id)
            n_new_posts += len(new_posts)

        logger.info("Got %d new posts", n_new_posts)

        return all_new_posts
