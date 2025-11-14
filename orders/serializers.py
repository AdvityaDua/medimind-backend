from rest_framework import serializers
from .models import Order, OrderItem
from .utils import match_medicine_by_name
from inventory.models import Inventory
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
        """
        Create an Order and update inventory by ADDING quantities (purchase order).
        """
        user = validated_data.get("user")
        items_data = validated_data.pop("items", [])

        # Wrap in a transaction to avoid partial state if something fails
        with transaction.atomic():
            order = Order.objects.create(**validated_data)

            for item in items_data:
                # Match medicine by normalized_name or product_name
                product_name = item.get("normalized_name") or item.get("product_name")
                medicine_obj = None
                if product_name:
                    medicine_obj = match_medicine_by_name(product_name)

                # Attach FK (may be None if no match)
                item["medicine"] = medicine_obj

                # Create the order item
                order_item = OrderItem.objects.create(order=order, **item)

                # Update inventory: ADD purchased quantity to stock
                if medicine_obj:
                    inv_entry, created = Inventory.objects.get_or_create(
                        user=user,
                        medicine=medicine_obj,
                        defaults={"quantity": 0, "unit_price": item.get("price") or None}
                    )

                    # Add quantity (ensure numeric types)
                    try:
                        add_qty = float(item.get("quantity") or 0)
                    except (TypeError, ValueError):
                        add_qty = 0.0

                    inv_entry.quantity = (inv_entry.quantity or 0) + add_qty

                    # If price provided, update unit_price (you can choose policy)
                    price = item.get("price")
                    if price is not None:
                        try:
                            inv_entry.unit_price = float(price)
                        except (TypeError, ValueError):
                            pass

                    inv_entry.save()

        return order