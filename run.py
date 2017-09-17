from Beemo import Beemo

import os

SHARD_ID = os.getenv("SHARD_ID")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB = os.getenv("REDIS_DB")

beemo = Beemo(shard_id=int(SHARD_ID), host=REDIS_HOST, port=int(REDIS_PORT), password=REDIS_PASSWORD, db=int(REDIS_DB))
beemo.run(beemo.token)
