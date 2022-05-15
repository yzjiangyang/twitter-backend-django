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