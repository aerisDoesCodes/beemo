import aioredis
import redis

from .storage import Storage

class DB(object):
    def __init__(self, shard_id, **kwargs):
        self.shard_id = shard_id
        self.kwargs = kwargs
        self.redis = redis.Redis(decode_responses=True, **kwargs)

    async def create_aioredis(self):
        self.redis = await aioredis.create_redis(
            (
                self.kwargs["host"],
                self.kwargs["port"]
            ),
            password=self.kwargs["password"],
            db=self.kwargs["db"],
            encoding="UTF-8"
        )
        self.cache_redis = await aioredis.create_redis(
            (
                self.kwargs["host"],
                self.kwargs["port"]
            ),
            password=self.kwargs["password"],
            db=4,
            encoding="UTF-8"
        )

    def get_storage(self, server):
        namespace = "server:{0}:".format(
            server.id,
        )
        storage = Storage(namespace, self.redis)
        return storage

    def get_shard_storage(self):
        namespace = "shard-{0}:".format(
            self.shard_id
        )
        storage = Storage(namespace, self.redis)
        return storage

    def get_namespace_storage(self, namespace):
        storage = Storage(namespace, self.redis)
        return storage
