from django.db.models import F

def incr_likes_count(sender, instance, created, **kwargs):
    from comments.models import Comment
    from tweets.models import Tweet

    if not created:
        return

    model_class = instance.content_object.__class__.__name__
    if model_class == 'Comment':
        # update does not trigger cache invalidate
        Comment.objects.filter(id=instance.object_id).update(
            likes_count=F('likes_count') + 1
        )
        return

    Tweet.objects.filter(id=instance.object_id).update(
        likes_count=F('likes_count') + 1
    )

def decr_likes_count(sender, instance, **kwargs):
    from comments.models import Comment
    from tweets.models import Tweet

    model_class = instance.content_object.__class__.__name__
    if model_class == 'Comment':
        Comment.objects.filter(id=instance.object_id).update(
            likes_count=F('likes_count') - 1
        )
        return

    Tweet.objects.filter(id=instance.object_id).update(
        likes_count=F('likes_count') - 1
    )