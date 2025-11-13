from django.db import models
from users.models import User



class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    order_id = models.CharField(max_length=100, unique=True)
    order_datetime = models.DateTimeField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    source = models.CharField(
        max_length=20,
        choices=[
            ("manual", "Manual"),
            ("pdf", "PDF Upload"),
            ('excel', "Excel Upload"),
        ],
        default="manual"
    )

    raw_receipt_text = models.TextField(null=True, blank=True)  # OCR text dump
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order_id}"
    
    


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    product_name = models.CharField(max_length=255)
    quantity = models.FloatField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Optional: useful for OCR confidence scoring
    confidence = models.FloatField(null=True, blank=True)

    # Optional: be ready for NLP structured data
    normalized_name = models.CharField(max_length=255, null=True, blank=True)
    medicine= models.ForeignKey(
        "Medicine", null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    



class Medicine(models.Model):
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, null=True, blank=True)
    requires_prescription = models.BooleanField(default=False)
    category = models.CharField(max_length=100, null=True, blank=True)