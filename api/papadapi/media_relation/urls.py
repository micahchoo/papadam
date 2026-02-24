from django.urls import path

from papadapi.media_relation.views import AnnotationRepliesView, MediaRefAnnotationsView

urlpatterns = [
    path(
        "replies/<uuid:annotation_uuid>/",
        AnnotationRepliesView.as_view(),
        name="annotation-replies",
    ),
    path(
        "media-refs/<uuid:media_uuid>/",
        MediaRefAnnotationsView.as_view(),
        name="media-ref-annotations",
    ),
]
