from accounts.services import UserService
from comments.listeners import decr_comments_count, incr_comments_count
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import pre_delete, post_save
from likes.models import Like
from tweets.models import Tweet
from utils.memcached.memcached_helper import MemcachedHelper


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)
    content = models.TextField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # de-normalization
    likes_count = models.IntegerField(default=0, null=True)

    class Meta:
        index_together = (('tweet', 'created_at'),)

    def __str__(self):
        return '{} - {} says {} at tweet {}'.format(
            self.created_at,
            self.user,
            self.content,
            self.tweet
        )

    @property
    def like_set(self):
        return Like.objects.filter(
            object_id=self.id,
            content_type=ContentType.objects.get_for_model(Comment)
        ).order_by('-created_at')

    @property
    def cached_user(self):
        return UserService.get_user_through_memcached(self.user_id)


pre_delete.connect(decr_comments_count, sender=Comment)
post_save.connect(incr_comments_count, sender=Comment)