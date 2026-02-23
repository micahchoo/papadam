from django.db.models import Count, F

from rest_framework import serializers

from papadapi.common.models import Group
from papadapi.archive.models import MediaStore
from papadapi.annotate.models import Annotation
from papadapi.common.functions import get_final_tags_count


from papadapi.users.models import User

# class MenuSerializer(serializers.ModelSerializer):
#     users = serializers.SerializerMethodField()

#     class Meta:
#         model = Menu
#         fields = ['id', 'food_name', 'users']

#     def get_users(self, obj):
#         users = User.objects.filter(pk__in=obj.order_set.all().values('user'))
#         return UserSerializer(users, many=True).data


# class OrderSerializer(serializers.HyperlinkedModelSerializer):
#     menu = MenuSerializer()
#     class Meta:
#         model = Order
#         fields = ['id', 'menu']

class GroupTagSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="tag_id")
    name = serializers.CharField(source="tags__name")
    count = serializers.IntegerField()


class UsersAPIGroupSerializer(serializers.ModelSerializer):

    
    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "description",
            "is_public",
            "created_at",
            "updated_at",
        )

        

class UserMEApiSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()
    media_count = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()
    # tags = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", 
            "username", 
            "first_name", 
            "last_name", 
            "is_superuser", 
            "groups",
            # "tags",
            "users_count",
            "media_count",
            )
        read_only_fields = ("username",)

    def get_groups(self, obj):
        groups_user_in = Group.objects.filter(users__in=[obj])
        return UsersAPIGroupSerializer(groups_user_in, many=True).data
    
    def get_media_count(self,obj):
        return 90

    def get_users_count(self,obj):
        return 82
    
    # def get_tags(self, obj):
    #     media_tags_count = (
    #         MediaStore.objects.filter(group=obj.id)
    #         .annotate(count=Count("tags"))
    #         .annotate(tag_id=F("tags__id"))
    #         .values("tag_id", "tags__name", "count")
    #         .order_by("-count")
    #     )
    #     annotation_tags_count = (
    #             Annotation.objects.filter(media_reference_id__in=list(MediaStore.objects.filter(group=obj.id)))
    #             .values("tags")
    #             .annotate(count=Count("tags"))
    #             .annotate(tag_id=F("tags__id"))
    #             .values("tag_id", "tags__name", "count")
    #             .order_by("-count")
    #         )
    #     tags_count = get_final_tags_count(list(media_tags_count),list(annotation_tags_count),count=True)
    #     return GroupTagSerializer(tags_count, many=True).data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name")
        read_only_fields = ("username",)


class UserStatsSerializer(serializers.Serializer):
    created_date = serializers.DateField()
    total = serializers.IntegerField()
