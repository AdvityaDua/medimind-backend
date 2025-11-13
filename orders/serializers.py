from rest_framework import serializers
from .models import Order, OrderItem, Medicine
from .utils import match_medicine_by_name


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
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)

        for item in items_data:

            # ----- AUTO MATCH MEDICINE NAME -----
            product_name = item.get("normalized_name") or item.get("product_name")
            medicine_obj = match_medicine_by_name(product_name)

            item["medicine"] = medicine_obj

            OrderItem.objects.create(order=order, **item)

        return order


class OrderItemResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "product_name",
            "normalized_name",
            "quantity",
            "price",
            "amount",
            "medicine"
        ]


class OrderResponseSerializer(serializers.ModelSerializer):
    items = OrderItemResponseSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "order_id",
            "order_datetime",
            "total_amount",
            "source",
            "items",
        ]