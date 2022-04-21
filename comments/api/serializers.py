from accounts.api.serializers import UserSerializerForComment
from comments.models import Comment
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from tweets.models import Tweet


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializerForComment()

    class Meta:
        model = Comment
        fields = ('id', 'user', 'tweet_id', 'content', 'created_at', 'updated_at')


class CommentSerializerForCreate(serializers.ModelSerializer):
    tweet_id = serializers.IntegerField()

    class Meta:
        model = Comment
        fields = ('tweet_id', 'content')

    def validate(self, data):
        tweet_id = data['tweet_id']
        if not Tweet.objects.filter(id=tweet_id).exists():
            raise ValidationError({
                'message': 'tweet does not exist.'
            })

        return data

    def create(self, validated_data):
        tweet_id = validated_data['tweet_id']
        content = validated_data['content']
        user = self.context['request'].user
        comment = Comment.objects.create(
            user=user,
            tweet_id=tweet_id,
            content=content,
        )
        return comment