from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Medicine, Inventory
from .serializers import MedicineSerializer, InventorySerializer


class MedicineViewSet(viewsets.ModelViewSet):
    serializer_class = MedicineSerializer

    def get_queryset(self):
        return Medicine.objects.filter(user=self.request.user).order_by("name")
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class InventoryViewSet(viewsets.ModelViewSet):
    serializer_class = InventorySerializer
    
    def get_queryset(self):
        return Inventory.objects.filter(user=self.request.user).order_by("-last_updated")
    
