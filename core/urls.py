from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    LogoutView,
    ImageUploadView,
    UserImageListView,
    ImageStatusView,
    ImageDeleteView,
    UserInfoView,
)


urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    
    # User Info
    path("user/info/", UserInfoView.as_view(), name="user_info"),
    
    # Image Upload
    path("images/upload/", ImageUploadView.as_view(), name="image_upload"),
    
    # Get User's Images
    path("images/", UserImageListView.as_view(), name="user_images"),
    path("images/status/<int:pk>/", ImageStatusView.as_view(), name="image_status"),
    path("images/<int:pk>/", ImageDeleteView.as_view(), name="image_delete"),
]
