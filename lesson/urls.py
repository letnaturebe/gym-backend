from django.urls import path

from lesson import views

urlpatterns = [
    path('', views.LessonAPIView.as_view(), name='lesson'),
    path('<int:pk>/', views.LessonDetailAPIView.as_view(), name='lesson-detail'),
    path('<int:pk>/reservation/', views.ReservationAPIView.as_view(), name='reservation'),
    path('reservation/<int:pk>/', views.ReservationDetailAPIView.as_view(), name='reservation-detail'),
]
