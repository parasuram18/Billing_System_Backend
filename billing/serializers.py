from rest_framework import serializers
from .models import ProductDetails, Denomination, Invoice, InvoiceItem


class DenominationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Denomination
        fields = ["value", "available_count"]


class ProductSerializer(serializers.ModelSerializer):
    price_with_tax = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = ProductDetails
        fields = [
            "id",
            "product_id",
            "name",
            "available_stocks",
            "price",
            "tax_percentage",
            "price_with_tax",
        ]

    def validate_tax_percentage(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Tax must be between 0–100")
        return value

    def validate_available_stocks(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative")
        return value
    

class InvoiceCreateSerializer(serializers.Serializer):
    
    customer_email = serializers.EmailField()
    products = serializers.ListField(child=serializers.DictField())
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceItem
        fields = [
            "product_name",
            "quantity",
            "price",
            "tax_percentage",
            "total_price"
        ]

    def get_total_price(self, obj):
        return obj.get_total().quantize(obj.price)
    

class InvoiceSerializer(serializers.ModelSerializer):
    purchased_at = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "purchased_at",
        ]
    def get_purchased_at(self, obj):
        return obj.created_at.strftime("%d-%m-%Y %I:%M %p")
    
    
class InvoiceDetailsSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    purchased_at = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "total_amount",
            "paid_amount",
            "balance_amount",
            "purchased_at",
            "items"
        ]
    def get_purchased_at(self, obj):
        return obj.created_at.strftime("%d-%m-%Y %I:%M %p")