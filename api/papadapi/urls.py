from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from papadapi.annotate.views import (
    AnnotationAddTag,
    AnnotationByMediaRetreiveSet,
    AnnotationCreateSet,
    AnnotationRemoveTag,
    AnnotationRetreiveSet,
    GroupAnnotationStats,
    InstanceAnnotationStats,
)
from papadapi.archive.views import (
    GroupMediaStats,
    InstanceMediaStats,
    MediaStoreAddTag,
    MediaStoreCopySet,
    MediaStoreCreateSet,
    MediaStoreRemoveTag,
    MediaStoreUpdateSet,
)
from papadapi.common.views import (
    AddCustomQuestionFromGroupView,
    AddUserFromGroupView,
    GroupTagGraphView,
    GroupViewSet,
    HealthCheck,
    InstanceGroupStats,
    RemoveCustomQuestionFromGroupView,
    RemoveUserFromGroupView,
    TagsViewSet,
    UpdateCustomQuestionFromGroupView,
    UpdateGroupViewSet,
)
from papadapi.importexport.views import (
    ExportGroupCreateListSet,
    ImportExportGroupViewSet,
    ImportGroupCreateSet,
    UserImportExportViewer,
)
from papadapi.users.views import InstanceUserStats, SearchUserView

router = DefaultRouter(trailing_slash=True)

# Users
router.register(r"users/search", SearchUserView, basename="SearchUserRoute")

# Archive
router.register(r"archive", MediaStoreUpdateSet, basename="MediaStoreUpdateRoute")
router.register(r"archive", MediaStoreCreateSet, basename="MediaStoreCreateRoute")
router.register(r"archive/copy", MediaStoreCopySet, basename="MediaStoreCopyRoute")
router.register(
    r"archive/remove_tag", MediaStoreRemoveTag, basename="MediaStoreRemoveTagRoute"
)
router.register(
    r"archive/add_tag", MediaStoreAddTag, basename="MediaStoreAddTagRoute"
)

# Common
router.register(r"tags", TagsViewSet, basename="TagsRoute")
router.register(r"group", GroupViewSet, basename="GroupRoute")
router.register(r"group", UpdateGroupViewSet, basename="UpdateGroupRoute")
router.register(
    r"group/remove_user", RemoveUserFromGroupView, basename="RemoveUserFromGroupRoute"
)
router.register(
    r"group/add_user", AddUserFromGroupView, basename="AddUserToGroupRoute"
)
router.register(
    r"group/remove_question",
    RemoveCustomQuestionFromGroupView,
    basename="RemoveQuestionFromGroupRoute",
)
router.register(
    r"group/add_question",
    AddCustomQuestionFromGroupView,
    basename="AddQuestionToGroupRoute",
)
router.register(
    r"group/update_question",
    UpdateCustomQuestionFromGroupView,
    basename="UpdateQuestionInGroupRoute",
)
router.register(
    r"group/taggraph", GroupTagGraphView, basename="GroupTagGraphRoute"
)

# Annotations
router.register(r"annotate", AnnotationCreateSet, basename="CreateAnnotationRoute")
router.register(
    r"annotate", AnnotationRetreiveSet, basename="RetrieveAnnotationRoute"
)
router.register(
    r"annotate/search",
    AnnotationByMediaRetreiveSet,
    basename="SearchAnnotationRoute",
)
router.register(
    r"annotate/remove_tag",
    AnnotationRemoveTag,
    basename="RemoveTagFromAnnotationRoute",
)
router.register(
    r"annotate/add_tag", AnnotationAddTag, basename="AddTagToAnnotationRoute"
)

# Import / Export
router.register(r"export", ExportGroupCreateListSet, basename="CreateExportRoute")
router.register(r"export", ImportExportGroupViewSet, basename="ExportRoute")
router.register(r"import", ImportGroupCreateSet, basename="CreateImportRoute")
router.register(r"import", ImportExportGroupViewSet, basename="ImportRoute")
router.register(
    r"myierequests", UserImportExportViewer, basename="UserImportExportRoute"
)

# Stats
router.register(
    r"instancegroupstats", InstanceGroupStats, basename="InstanceGroupStatsRoute"
)
router.register(
    r"instanceuserstats", InstanceUserStats, basename="InstanceUserStatsRoute"
)
router.register(
    r"instancemediastats", InstanceMediaStats, basename="InstanceMediaStatsRoute"
)
router.register(
    r"instanceannotationstats",
    InstanceAnnotationStats,
    basename="InstanceAnnotationStatsRoute",
)
router.register(
    r"groupannotationstats",
    GroupAnnotationStats,
    basename="GroupAnnotationStatsRoute",
)
router.register(
    r"groupmediastats", GroupMediaStats, basename="GroupMediaStatsRoute"
)


urlpatterns = [
    # ── API v1 ────────────────────────────────────────────────────────────────
    path("api/v1/", include(router.urls)),
    path("api/v1/crdt/", include("papadapi.crdt.urls")),
    path("api/v1/events/", include("papadapi.events.urls")),
    path("api/v1/exhibit/", include("papadapi.exhibit.urls")),
    path("api/v1/media-relation/", include("papadapi.media_relation.urls")),

    # ── Auth — djoser (user management) + simplejwt (tokens) ─────────────────
    re_path(r"^auth/", include("djoser.urls")),
    path("auth/jwt/create/", TokenObtainPairView.as_view(), name="jwt-create"),
    path("auth/jwt/refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
    path("auth/jwt/verify/", TokenVerifyView.as_view(), name="jwt-verify"),

    # ── OpenAPI schema & docs ─────────────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path("nimda/", admin.site.urls),

    # ── Health ────────────────────────────────────────────────────────────────
    path("healthcheck/", HealthCheck.as_view(), name="healthcheck"),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
