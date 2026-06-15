from django.urls import path

from apps.normalization.views import LowConfidenceQueueView

urlpatterns = [
    path("normalization/low-confidence/", LowConfidenceQueueView.as_view(), name="low-confidence-events"),
]
