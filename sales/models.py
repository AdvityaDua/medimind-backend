from django.db import models
from users.models import User
from inventory.models import Medicine

class Sale(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    sale_id = models.CharField(max_length=100, unique=True)
    sale_datetime = models.DateTimeField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    source = models.CharField(
        max_length=20,
        choices=[
            ("manual", "Manual"),
            ("pdf", "PDF Upload"),
            ("excel", "Excel Upload"),
        ],
        default="manual"
    )

    raw_receipt_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sale {self.sale_id}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")

    product_name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255, null=True, blank=True)

    quantity = models.FloatField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    medicine = models.ForeignKey(
        Medicine,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sales_items"
    )

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"