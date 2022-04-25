from accounts.api.serializers import UserSerializerForLike
from comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from likes.models import Like
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from tweets.models import Tweet


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializerForLike()

    class Meta:
        model = Like
        fields = ('user', 'created_at')


class LikeSerializerForCreate(serializers.ModelSerializer):
    content_type = serializers.ChoiceField(choices=['tweet', 'comment'])
    object_id = serializers.IntegerField()

    class Meta:
        model = Like
        fields = ('content_type', 'object_id')

    def _get_model_class(self, data):
        model_class = data['content_type']
        if model_class == 'tweet':
            return Tweet
        if model_class == 'comment':
            return Comment

        return None

    def validate(self, data):
        model_class = self._get_model_class(data)
        if model_class == None:
            raise ValidationError({'content_type': 'Content type does not exist'})
        if not model_class.objects.filter(id=data['object_id']).exists():
            raise ValidationError({'object_id': 'Object does not exist'})

        return data

    def create(self, validated_data):
        model_class = self._get_model_class(validated_data)
        like, _ = Like.objects.get_or_create(
            object_id=validated_data['object_id'],
            content_type=ContentType.objects.get_for_model(model_class),
            user=self.context['request'].user,
        )

        return like