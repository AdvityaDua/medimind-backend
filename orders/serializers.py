from rest_framework import serializers
from .models import Order, OrderItem
from .utils import match_medicine_by_name
from inventory.models import Inventory, Medicine
from django.db import transaction


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_name",
            "quantity",
            "price",
            "amount",
            "confidence",
            "normalized_name",
            "medicine",
        ]



class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "order_id",
            "order_datetime",
            "total_amount",
            "source",
            "raw_receipt_text",
            "items",
        ]

    def create(self, validated_data):
        user = validated_data.get("user")
        items_data = validated_data.pop("items", [])

        with transaction.atomic():
            order = Order.objects.create(**validated_data)

            for item in items_data:
                # Try to match medicine by normalized or original name
                product_name = item.get("normalized_name") or item.get("product_name")

                medicine_obj = None
                if product_name:
                    medicine_obj = match_medicine_by_name(product_name)

                # ---------------------------------------------------------
                # AUTO-CREATE MEDICINE IF IT DOES NOT EXIST
                # ---------------------------------------------------------
                if medicine_obj is None:
                    medicine_obj = Medicine.objects.create(
                        user=user,
                        name=product_name,
                        generic_name=None,
                        requires_prescription=False,
                        category=None,
                    )

                    # Create base inventory entry
                    Inventory.objects.create(
                        user=user,
                        medicine=medicine_obj,
                        quantity=0,
                        unit_price=item.get("price") or None,
                    )

                # attach FK
                item["medicine"] = medicine_obj

                # Create the order item
                order_item = OrderItem.objects.create(order=order, **item)

                # ---------------------------------------------------------
                # UPDATE INVENTORY QUANTITY (ADD)
                # ---------------------------------------------------------
                inv_entry = Inventory.objects.get(user=user, medicine=medicine_obj)

                try:
                    add_qty = float(item.get("quantity") or 0)
                except (TypeError, ValueError):
                    add_qty = 0.0

                inv_entry.quantity = (inv_entry.quantity or 0) + add_qty

                # Update unit price if given
                price = item.get("price")
                if price is not None:
                    try:
                        inv_entry.unit_price = float(price)
                    except (TypeError, ValueError):
                        pass

                inv_entry.save()

        return order


class MedicineResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = [
            "id",
            "name",
            "generic_name",
            "requires_prescription",
            "category"
        ]
class OrderItemResponseSerializer(serializers.ModelSerializer):
    medicine = MedicineResponseSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_name",
            "quantity",
            "price",
            "amount",
            "confidence",
            "normalized_name",
            "medicine",
        ]


class OrderResponseSerializer(serializers.ModelSerializer):
    items = OrderItemResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "order_datetime",
            "total_amount",
            "source",
            "raw_receipt_text",
            "items",
            "created_at",
        ]
