from django.urls import path

from papadapi.crdt.views import YDocStateView

urlpatterns = [
    path("<uuid:media_uuid>/", YDocStateView.as_view(), name="crdt-doc-state"),
]
