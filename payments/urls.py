# payments/urls.py
from django.urls import path
from .views import ListBankAccountsView, ListPaymentInstructionsView, AdminBankAccountView

urlpatterns = [
    # Public endpoints
    path('accounts/', ListBankAccountsView.as_view(), name='list-bank-accounts'),
    path('instructions/', ListPaymentInstructionsView.as_view(), name='list-payment-instructions'),
    
    # Admin endpoints
    path('admin/accounts/', AdminBankAccountView.as_view(), name='admin-bank-accounts'),
]