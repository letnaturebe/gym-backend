from django.urls import path

from user import views

urlpatterns = [
    path('', views.UserAPIView.as_view(), name='user'),
    path('<int:pk>/', views.UserDetailAPIView.as_view(), name='user-detail'),
]
