from django.urls import path
from .views import JobListView, LocationListView, LocationFieldListView

urlpatterns = [
    path("jobs/", JobListView.as_view(), name="job-list"),
    path("locations/", LocationListView.as_view(), name="location-list"),
    path(
        "location-field/", LocationFieldListView.as_view(), name="location-field-list"
    ),
]
