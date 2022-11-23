from django.urls import path

from credit import views

urlpatterns = [
    path('', views.CreditAPIView.as_view(), name='credit'),
    path('price-policy/', views.PricePolicyAPIView.as_view(), name='price-policy'),
]
