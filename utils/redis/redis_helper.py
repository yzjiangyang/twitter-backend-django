from django.conf import settings
from utils.redis.redis_client import RedisClient
from utils.redis.redis_serializers import DjangoModelSerializer


class RedisHelper:

    @classmethod
    def _load_objects_to_cache(cls, key, queryset):
        conn = RedisClient.get_connection()
        serialized_list = []
        for obj in queryset[:settings.REDIS_LIST_LENGTH_LIMIT]:
            serialized_data = DjangoModelSerializer.serialize(obj)
            serialized_list.append(serialized_data)

        if serialized_list:
            conn.rpush(key, *serialized_list)

    @classmethod
    def load_objects(cls, key, queryset):
        conn = RedisClient.get_connection()
        if conn.exists(key):
            serialized_list = conn.lrange(key, 0, -1)
            objects = []
            for serialized_data in serialized_list:
                deserialized_data = DjangoModelSerializer.deserializer(serialized_data)
                objects.append(deserialized_data)
            return objects

        cls._load_objects_to_cache(key, queryset)
        return list(queryset)

    @classmethod
    def push_object(cls, key, obj, queryset):
        conn = RedisClient.get_connection()
        if not conn.exists(key):
            cls._load_objects_to_cache(key, queryset)
            return

        serialized_data = DjangoModelSerializer.serialize(obj)
        conn.lpush(key, serialized_data)
        conn.ltrim(key, 0, settings.REDIS_LIST_LENGTH_LIMIT - 1)

    @classmethod
    def get_key(cls, obj, attr):
        return '{}.{}:{}'.format(obj.__class__.__name__, attr, obj.id)

    @classmethod
    def incr_count(cls, obj, attr):
        key = cls.get_key(obj, attr)
        conn = RedisClient.get_connection()
        if conn.exists(key):
            return conn.incr(key, 1) # increase count by 1 and return

        # refresh form db, don't need to add 1 before set key value
        obj.refresh_from_db()
        conn.set(key, getattr(obj, attr))
        conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
        return getattr(obj, attr)

    @classmethod
    def decr_count(cls, obj, attr):
        key = cls.get_key(obj, attr)
        conn = RedisClient.get_connection()
        if conn.exists(key):
            return conn.decr(key, 1)

        # refresh form db, don't need to minus 1 before set key value
        obj.refresh_from_db()
        conn.set(key, getattr(obj, attr))
        conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)
        return getattr(obj, attr)

    @classmethod
    def get_count(cls, obj, attr):
        key = cls.get_key(obj, attr)
        conn = RedisClient.get_connection()
        if conn.exists(key):
            return int(conn.get(key)) # use int(), otherwise, return b'1'

        # refresh, because not sure obj is retrieved from db or cache
        obj.refresh_from_db()
        conn.set(key, getattr(obj, attr))
        return getattr(obj, attr)