from django.contrib import admin
from .models import ProductDetails, Denomination


@admin.register(Denomination)
class DenominationAdmin(admin.ModelAdmin):
    list_display = (
        "value",
        "available_count"
    )

@admin.register(ProductDetails)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_id",
        "name",
        "available_stocks",
        "price",
        "is_active",
        "tax_percentage",
        "price_with_tax",
    )
    search_fields = ("name", "product_id")
    list_filter = ("tax_percentage",)