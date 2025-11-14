from rest_framework import serializers
from .models import Medicine, Inventory


class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = [
            "id",
            "name",
            "generic_name",
            "requires_prescription",
            "category",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        medicine = Medicine.objects.create( **validated_data)
        Inventory.objects.create(user=user, medicine=medicine, quantity=0)
        return medicine


class InventorySerializer(serializers.ModelSerializer):
    medicine_detail = MedicineSerializer(source="medicine", read_only=True)

    class Meta:
        model = Inventory
        fields = [
            "id",
            "medicine",
            "medicine_detail",
            "quantity",
            "unit_price",
            "last_updated",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        return Inventory.objects.create(user=user, **validated_data)