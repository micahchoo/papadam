from django.urls import path

from papadapi.events.views import JobStatusView

urlpatterns = [
    path("jobs/<str:job_id>/", JobStatusView.as_view(), name="job-status"),
]
