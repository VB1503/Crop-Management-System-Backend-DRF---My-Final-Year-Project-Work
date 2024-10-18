from django.urls import path, include
from .views import CropRecomendationApiView,ListCreateLandmarkAPIView,CropYieldPredictionView,FertilizerRecommendation,PusherEventTrigger,DeleteLandmarkAPIView
urlpatterns=[
    path('croprecommendation/',CropRecomendationApiView.as_view(),name='crop recommendation'),
    path('cropyield/',CropYieldPredictionView.as_view(),name='cropyield'),
    path('fertilizer/',FertilizerRecommendation.as_view(),name="fertilizer"),
    path('trigger-event/', PusherEventTrigger.as_view(), name='trigger_event'),
    path('landmark/', ListCreateLandmarkAPIView.as_view(), name='landmark-list-create'),
    path('landmark/delete/<int:user_id>/<int:landId>/', DeleteLandmarkAPIView.as_view(), name='delete-landmark'),
    path('landmarks/<int:pk>/', ListCreateLandmarkAPIView.as_view(), name='landmark-detail')
]