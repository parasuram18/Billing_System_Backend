from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class CustomUser(AbstractUser):
    
    email = models.EmailField(max_length=50, blank=True, null=True)



from django.db import models
from decimal import Decimal


class ProductDetails(models.Model):
    
    product_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    available_stocks = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ["name"]
        db_table = "product_details"

    def __str__(self):
        return f"{self.name} ({self.product_id})"

    @property
    def price_with_tax(self):
        tax_amount = (self.price * self.tax_percentage) / Decimal("100")
        return self.price + tax_amount
    

class Denomination(models.Model):

    value = models.PositiveIntegerField(unique=True)
    available_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.value}"
    

class Invoice(models.Model):

    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class InvoiceItem(models.Model):

    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(ProductDetails, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2)

    def get_total(self):
        tax = (self.price * self.tax_percentage) / 100
        return (self.price + tax) * self.quantity