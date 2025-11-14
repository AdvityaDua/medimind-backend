from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Medicine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="medicines", null=True, blank=True)
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, null=True, blank=True)
    requires_prescription = models.BooleanField(default=False)
    category = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name


class Inventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="inventory", null=True, blank=True)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="inventory_items")
    quantity = models.FloatField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.medicine.name} - {self.quantity}"