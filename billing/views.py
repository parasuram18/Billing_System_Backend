from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import CustomUser, ProductDetails, Denomination, Invoice, InvoiceItem
from .serializers import InvoiceDetailsSerializer, InvoiceSerializer, ProductSerializer, InvoiceCreateSerializer, DenominationSerializer
from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from threading import Thread
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.conf import settings


def billing_page(request):

    denomination_objs = Denomination.objects.order_by("-value")
    denominations = DenominationSerializer(denomination_objs, many=True).data
    return render(request, "billing_page.html", {
        "denominations": denominations
    })

def product_page(request):
    return render(request, "products.html")

class ProductListCreateAPIView(APIView):

    def get(self, request):
        try:

            products = ProductDetails.objects.all()
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            return Response({"status":"Error", "message":f"{str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            serializer = ProductSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status":"Error", "message":f"{str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    
class ProductDetailAPIView(APIView):

    def get_object(self, pk):
        return get_object_or_404(ProductDetails, pk=pk)

    def get(self, request, pk):
        try:
            product = self.get_object(pk)
            serializer = ProductSerializer(product)
            return Response(serializer.data)
        except Exception as e:
            return Response({"status":"Error", "message":f"{str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            product = self.get_object(pk)
            serializer = ProductSerializer(product, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"status":"Error", "message":f"{str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            product = self.get_object(pk)
            product.is_active = False
            product.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({"status":"Error", "message":f"{str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class InvoiceCreateAPIView(APIView):

    def calculate_denominations(self, balance_amount):

        denominations = Denomination.objects.order_by("-value")
        result = {}
        remaining = int(balance_amount)

        for denom in denominations:
            if remaining <= 0:
                break

            count = min(remaining // denom.value, denom.available_count)

            if count > 0:
                result[denom.value] = int(count)
                remaining -= denom.value * count

        return result

    def send_invoice_email(self, email, invoice_data):

        subject = f"Invoice #{invoice_data['invoice_id']}"
        
        html_content = render_to_string(
            "invoice_email.html",
            invoice_data
        )

        email_message = EmailMultiAlternatives(
            subject=subject,
            body="Your invoice is attached below.",  # fallback text
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )

        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

    def post(self, request):
        try:
            serializer = InvoiceCreateSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(serializer.errors, status=400)

            data = serializer.validated_data
            User = get_user_model()

            transaction.set_autocommit(False)

            customer, _ = User.objects.get_or_create(
                email=data["customer_email"],
                defaults={"username": data["customer_email"]}
            )

            total_without_tax = Decimal("0.00")
            total_tax = Decimal("0.00")
            item_details = []

            # Validate & Calculate
            for item in data["products"]:
                product = ProductDetails.objects.select_for_update().filter(
                    product_id=item["product_id"]
                ).first()

                if not product:
                    return Response({"status":"error", "message": "Invalid product"}, status=400)

                quantity = int(item["quantity"])

                if product.available_stocks < quantity:
                    return Response({"status":"error", "message": "Insufficient stock"}, status=400)

                item_price = product.price
                tax_amount = (item_price * product.tax_percentage) / 100
                purchase_price = item_price * quantity
                total_tax_item = tax_amount * quantity
                total_item_price = (item_price + tax_amount) * quantity

                total_without_tax += purchase_price
                total_tax += total_tax_item

                item_details.append({
                    "product_id": product.product_id,
                    "unit_price": item_price,
                    "quantity": quantity,
                    "purchase_price": purchase_price,
                    "tax_percent": product.tax_percentage,
                    "tax_payable": total_tax_item,
                    "total_price": total_item_price,
                    "product_name": product.name
                })

            net_price = total_without_tax + total_tax
            rounded_down_net = net_price.quantize(Decimal("1.00"))  # round to whole
            paid_amount = data["paid_amount"]
            
            if paid_amount < rounded_down_net:
                return Response({"status":"error", "message": "Paid amount insufficient"}, status=400)

            balance_amount = paid_amount - rounded_down_net

            # Save Invoice
            invoice = Invoice.objects.create(
                customer=customer,
                total_amount=rounded_down_net,
                paid_amount=paid_amount,
                balance_amount=balance_amount
            )

            for item in item_details:
                product_obj = ProductDetails.objects.get(product_id = item["product_id"])
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product_obj,
                    quantity=item["quantity"],
                    price=item["unit_price"],
                    tax_percentage=item["tax_percent"]
                )

                product_obj.available_stocks -= item["quantity"]
                product_obj.save()

            # Calculate Balance Denomination
            denomination_result = self.calculate_denominations(balance_amount)

            invoice_data = {
                "invoice_id": invoice.id,
                "customer_email": customer.email,
                "product_details": item_details,
                "total_without_tax": total_without_tax,
                "total_tax": total_tax,
                "net_price": net_price,
                "rounded_net_price": rounded_down_net,
                "balance_amount": balance_amount,
                "denominations": denomination_result
            }

            # Email to customer
            Thread(
                target=self.send_invoice_email,
                args=(customer.email, invoice_data)
            ).start()

            transaction.commit()

            return Response({
                "invoice_id": invoice.id,
                "customer_email": customer.email,
                "items": item_details,
                "total_without_tax": total_without_tax,
                "total_tax": total_tax,
                "net_price": net_price,
                "rounded_net_price": rounded_down_net,
                "balance_amount": balance_amount,
                "denominations": denomination_result
            })
        except Exception as e:
            transaction.rollback()
            return Response({"status":"error", "message": str(e)})
        

class CustomerInvoicesAPIView(APIView):

    def get(self, request):
        try:
            email = request.GET.get("email")

            if not email:
                return Response({"status":"error", "message": "Email required"}, status=400)

            customer = CustomUser.objects.filter(email=email).first()
            if not customer:
                return Response({"status":"error", "message": "Customer not found"}, status=404)

            invoices = Invoice.objects.filter(customer=customer).order_by("-created_at")

            serializer = InvoiceSerializer(invoices, many=True)

            return Response(serializer.data)
        except Exception as e:
            return Response({"status":"error", "message":f"{str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            
class GetInvoiceDetails(APIView):

    def get(self, request, pk):
        try:

            invoice_obj = get_object_or_404(Invoice, id=pk)
            serializer = InvoiceDetailsSerializer(invoice_obj)
            return Response(serializer.data)
        
        except Exception as e:
            return Response({"status":"Error", "message":f"{str(e)}"}, status=status.HTTP_400_BAD_REQUEST)