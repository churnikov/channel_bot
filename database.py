import logging
from typing import List

from dependencies import Injector
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

fh = logging.FileHandler("channels_bot.log")
fh.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)


class ProcessResource:
    def __init__(self, mc: MongoClient, db_name: str, collection_name: str):
        self.collection_name = collection_name
        self.db_name = db_name
        self.mc = mc
        self.db = self.mc[self.db_name]
        self.collection = self.db[self.collection_name]


class AddNewResource(ProcessResource):
    def __call__(self, channel_name: str, channel_id: int, post_id: int) -> None:
        channel = self.collection.find_one({"_id": channel_id})

        if channel is None:
            logger.info("Tracking channel %s", channel_name)
            self.collection.insert_one(
                {"_id": channel_id, "name": channel_name, "recent_post_id": post_id}
            )
        elif channel["name"] != channel_name:
            logger.info("Channel %s has been renamed to %s", channel["name"], channel_name)
            self.collection.update_one({"_id": channel_id}, {"$set": {"name": channel_name}})


class UpdateRecentId(ProcessResource):
    def __call__(self, channel_id: int, post_id: int) -> None:

        self.collection.update_one({"_id": channel_id}, {"$set": {"recent_post_id": post_id}})

        logger.debug("Channels %d new recent id post is %d", channel_id, post_id)


class GetRecentId(ProcessResource):
    def __call__(self, channel_id: int) -> int:

        result = self.collection.find_one({"_id": channel_id}, {"recent_post_id": 1})

        return result["recent_post_id"]


class Iter(ProcessResource):
    def __call__(self):

        return self.collection.find()


class GetResourcesNames(ProcessResource):
    def __call__(self, channel_ids: List[int]) -> List[str]:
        return [c["name"] for c in self.collection.find({"_id": {"$in": channel_ids}}, {"name": 1})]


class AddNewUser(ProcessResource):
    def __call__(self, user_id: int) -> bool:
        try:
            self.collection.insert_one({"_id": user_id, "subscriptions": []})
            logger.info("Added new user %d", user_id)
            return True
        except DuplicateKeyError:
            return False


class Subscribe(ProcessResource):
    def __call__(self, user_id: int, channel_id: int) -> None:
        self.collection.update_one({"_id": user_id}, {"$addToSet": {"subscriptions": channel_id}})
        logger.info("User %d subscribed to %d", user_id, channel_id)


class Unsubscribe(ProcessResource):
    def __call__(self, user_id: int, channel_id: int) -> None:
        self.collection.update_one({"_id": user_id}, {"$pull": {"subscriptions": channel_id}})
        logger.info("User %d unsubscribed from %d", user_id, channel_id)


class ListSubscriptions(ProcessResource):
    def __call__(self, user_id: int) -> List[int]:
        return self.collection.find_one({"_id": user_id}, {"subscriptions": 1})["subscriptions"]


class ResourcesContainer(Injector):
    add_new_resource = AddNewResource
    update_recent_id = UpdateRecentId
    get_recent_id = GetRecentId
    get_resources_names = GetResourcesNames
    iterate = Iter
    mc = MongoClient()
    db_name = "channels_bot"
    collection_name = "resources"


class UserContainer(Injector):
    add_new_user = AddNewUser
    subscribe = Subscribe
    unsubscribe = Unsubscribe
    list_subscriptions = ListSubscriptions
    iterate = Iter
    mc = MongoClient()
    db_name = "channels_bot"
    collection_name = "users"
