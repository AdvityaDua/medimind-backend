from django.urls import path
from .views import OrderViewSet


urlpatterns = [
    path('', OrderViewSet.as_view({'get': 'list', 'post': 'create'}), name='order-list'),
]
