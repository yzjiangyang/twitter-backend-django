from accounts.listeners import user_profile_change, user_change
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete, post_save
from utils.memcached.listeners import invalidate_object_cache


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    avatar = models.FileField(null=True)
    nickname = models.CharField(null=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} {}'.format(self.user, self.nickname)

def get_profile(user):
    if hasattr(user, '_cached_user_profile'):
        return user._cached_user_profile

    from accounts.services import UserService
    profile = UserService.get_profile_through_memcached(user.id)
    setattr(user, '_cached_user_profile', profile)
    return profile

User.profile = property(get_profile)


pre_delete.connect(user_change, sender=User)
post_save.connect(user_change, sender=User)
pre_delete.connect(user_profile_change, sender=UserProfile)
post_save.connect(user_profile_change, sender=UserProfile)