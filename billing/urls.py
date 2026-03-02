from django.urls import path
from .views import (
    CustomerInvoicesAPIView,
    ProductListCreateAPIView,
    ProductDetailAPIView,
    product_page,
    billing_page,
    InvoiceCreateAPIView,
    GetInvoiceDetails
)

urlpatterns = [

    path("products/", ProductListCreateAPIView.as_view(), name="product-list"),

    path("products/<int:pk>/", ProductDetailAPIView.as_view(), name="product-detail"),

    # path("products_home/", product_page, name="product-page"),

    path("billing/", billing_page, name="billing-page"),

    path("create/invoice/", InvoiceCreateAPIView.as_view(), name="create-invoice"),  

    path("customer/invoices/", CustomerInvoicesAPIView.as_view()),  

    path("invoice/<int:pk>/", GetInvoiceDetails.as_view()),  

]