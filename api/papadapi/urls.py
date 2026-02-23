from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path, reverse_lazy

# from django.contrib import admin
from django.views.generic.base import RedirectView
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter, SimpleRouter

from papadapi.archive.views import (
    GroupMediaStats,
    InstanceMediaStats,
    MediaStoreAddTag,
    MediaStoreRemoveTag,
)

# Common Imports
from papadapi.common.views import (
    AddCustomQuestionFromGroupView,
    GroupViewSet,
    InstanceGroupStats,
    RemoveCustomQuestionFromGroupView,
    AddUserFromGroupView,
    RemoveUserFromGroupView,
    TagsViewSet,
    UpdateCustomQuestionFromGroupView,
    UpdateGroupViewSet,
    GroupTagGraphView,
    RedirectToUIView,
    HealthCheck
)
from papadapi.importexport.views import (
    ExportGroupCreateListSet,
    ImportExportGroupViewSet,
    ImportGroupCreateSet,
    UserImportExportViewer,
)

# Annotate Imports
from .annotate.views import (
    AnnotationByMediaRetreiveSet,
    AnnotationCreateSet,
    AnnotationRetreiveSet,
    AnnotationAddTag,
    AnnotationRemoveTag,
    GroupAnnotationStats,
    InstanceAnnotationStats,
)

# Archive Imports
from .archive.views import MediaStoreCopySet, MediaStoreCreateSet, MediaStoreUpdateSet

# User Imports
from .users.views import InstanceUserStats, SearchUserView

# Import Export Views

router = DefaultRouter(trailing_slash=True)
router.register(r"users/search", SearchUserView, basename="SearchUserRoute")
router.register(r"archive", MediaStoreUpdateSet, basename="MediaStoreUpdateRoute")
router.register(r"archive", MediaStoreCreateSet, basename="MediaStoreCreateRoute")
router.register(r"archive/copy", MediaStoreCopySet, basename="MediaStoreCopyRoute")
router.register(r"archive/remove_tag", MediaStoreRemoveTag, basename="MediaStoreRemoveTagRoute")
router.register(r"archive/add_tag", MediaStoreAddTag, basename="MediaStoreAddTagRoute")
router.register(r"tags", TagsViewSet, basename="TagsRoute")
router.register(r"group", GroupViewSet, basename="GroupRoute")
router.register(r"group", UpdateGroupViewSet, basename="UpdateGroupRoute")
router.register(r"group/remove_user", RemoveUserFromGroupView, basename="RemoveUserFromGroupRoute")
router.register(r"group/add_user", AddUserFromGroupView, basename="AddUserToGroupRoute")
router.register(r"group/remove_question", RemoveCustomQuestionFromGroupView, basename="RemoveQuestionFromGroupRoute")
router.register(r"group/add_question", AddCustomQuestionFromGroupView, basename="AddQuestionToGroupRoute")
router.register(r"group/update_question", UpdateCustomQuestionFromGroupView, basename="UpdateQuestionInGroupRoute")
router.register(r"annotate", AnnotationCreateSet, basename="CreateAnnotationRoute")
router.register(r"annotate", AnnotationRetreiveSet, basename="RetrieveAnnotationRoute")
router.register(r"annotate/search", AnnotationByMediaRetreiveSet, basename="SearchAnnotationRoute")
router.register(r"annotate/remove_tag", AnnotationRemoveTag, basename="RemoveTagFromAnnotationRoute")
router.register(r"annotate/add_tag", AnnotationAddTag, basename="AddTagToAnnotationRoute")
router.register(r"export", ExportGroupCreateListSet, basename="CreateExportRoute")
router.register(r"export", ImportExportGroupViewSet, basename="ExportRoute")
router.register(r"import", ImportGroupCreateSet, basename="CreateImportRoute")
router.register(r"import", ImportExportGroupViewSet, basename="ImportRoute")
router.register(r"myierequests", UserImportExportViewer, basename="UserImportExportRoute")
router.register(r"instancegroupstats", InstanceGroupStats, basename="InstanceGroupStatsRoute")
router.register(r"instanceuserstats", InstanceUserStats, basename="InstanceUserStatsRoute")
router.register(r"instancemediastats", InstanceMediaStats, basename="InstanceMediaStatsRoute")
router.register(r"instanceannotationstats", InstanceAnnotationStats, basename="InstanceAnnotationStatsRoute")
router.register(r"groupannotationstats", GroupAnnotationStats, basename="GroupAnnotationStatsRoute")
router.register(r"groupmediastats", GroupMediaStats, basename="GroupMediaStatsRoute")
router.register(r"group/taggraph", GroupTagGraphView, basename="GroupTagGraphRoute")



urlpatterns = [
    # path('admin/', admin.site.urls),
    path("api/v1/", include(router.urls)),
    re_path(r"^auth/", include("djoser.urls")),
    re_path(r"^auth/", include("djoser.urls.authtoken")),
    path("ui/",include("papadapi.pages.urls")),
    path("nimda/", admin.site.urls),
    path('healthcheck/', HealthCheck.as_view(), name='healthcheck'),
    # the 'api-root' from django rest-frameworks default router
    # http://www.django-rest-framework.org/api-guide/routers/#defaultrouter
    re_path(r"^$",RedirectToUIView.as_view()),
    path("about/", RedirectToUIView.as_view()),
    re_path(r'^collection/(?P<collection_id>\d+)$',RedirectToUIView.as_view()),
    re_path(r'^collection/(?P<collection_id>\d+)/media/(?P<media_id>[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})$',RedirectToUIView.as_view()),
    re_path(r'^collection/(?P<collection_id>\d+)/media/(?P<media_id>[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})/annotation/(?P<annotation_id>[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})$',RedirectToUIView.as_view())
] #+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
