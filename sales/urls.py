from django.urls import path
from .views import SaleViewSet

urlpatterns = [
    path('', SaleViewSet.as_view({'get': 'list', 'post': 'create'}), name='sale-list'),
]
