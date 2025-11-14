from rest_framework import serializers
from .models import Sale, SaleItem
from inventory.models import Inventory, Medicine
from .utils import match_medicine_by_name
from django.db import transaction


class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = [
            "id",
            "product_name",
            "quantity",
            "price",
            "amount",
            "normalized_name",
            "medicine",
        ]


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)

    class Meta:
        model = Sale
        fields = [
            "id",
            "user",
            "sale_id",
            "sale_datetime",
            "total_amount",
            "source",
            "raw_receipt_text",
            "items",
        ]

    def create(self, validated_data):
        user = validated_data["user"]
        items_data = validated_data.pop("items")

        with transaction.atomic():
            sale = Sale.objects.create(**validated_data)

            for item in items_data:
                # Normalize name
                product_name = item.get("normalized_name") or item["product_name"]
                medicine_obj = match_medicine_by_name(product_name)
                item["medicine"] = medicine_obj

                sale_item = SaleItem.objects.create(sale=sale, **item)

                # Inventory adjustment: SUBTRACT stock
                if medicine_obj:
                    inv, _ = Inventory.objects.get_or_create(
                        user=user, medicine=medicine_obj, defaults={"quantity": 0}
                    )

                    try:
                        qty = float(item["quantity"])
                    except:
                        qty = 0

                    inv.quantity = max(inv.quantity - qty, 0)
                    inv.save()

        return sale