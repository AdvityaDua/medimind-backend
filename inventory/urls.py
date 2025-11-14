from django.urls import path
from .views import MedicineViewSet, InventoryViewSet


urlpatterns = [
    path('medicines/', MedicineViewSet.as_view({'get': 'list', 'post': 'create'}), name='medicine-list'),
    path('', InventoryViewSet.as_view({'get': 'list'}), name='inventory-list'),
]
