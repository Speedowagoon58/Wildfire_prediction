from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PredictionViewSet, dashboard

app_name = "predictions"

router = DefaultRouter()
router.register(r"results", PredictionViewSet, basename="predictionresult")

# The API URLs are now determined automatically by the router.
# This includes:
# - /results/ (list)
# - /results/{pk}/ (retrieve)
# - /results/predict-for-region/ (custom action)
urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("api/", include(router.urls)),
]
