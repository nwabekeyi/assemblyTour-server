from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework import status
from django.http import JsonResponse
from .models import BankAccount, PaymentInstruction


class ListBankAccountsView(APIView):
    """Public endpoint to list active bank accounts."""
    permission_classes = [AllowAny]

    def get(self, request):
        accounts = BankAccount.objects.filter(is_active=True).order_by("-is_primary", "bank_name")
        data = [
            {
                "id": acc.id,
                "bank_name": acc.bank_name,
                "account_name": acc.account_name,
                "account_number": acc.account_number,
                "account_type": acc.account_type,
                "notes": acc.notes,
                "is_primary": acc.is_primary,
            }
            for acc in accounts
        ]
        return JsonResponse({"success": True, "bank_accounts": data})


class ListPaymentInstructionsView(APIView):
    """Public endpoint to get payment instructions."""
    permission_classes = [AllowAny]

    def get(self, request):
        instructions = PaymentInstruction.objects.filter(is_active=True).order_by("order")
        data = [
            {
                "id": ins.id,
                "title": ins.title,
                "content": ins.content,
            }
            for ins in instructions
        ]
        return JsonResponse({"success": True, "instructions": data})


class AdminBankAccountView(APIView):
    """Admin-only endpoints for managing bank accounts."""
    permission_classes = [IsAdminUser]

    def post(self, request):
        data = request.POST or request.data
        
        if not data.get("bank_name") or not data.get("account_name") or not data.get("account_number"):
            return JsonResponse({"success": False, "message": "Missing required fields"}, status=400)

        bank = BankAccount.objects.create(
            bank_name=data["bank_name"],
            account_name=data["account_name"],
            account_number=data["account_number"],
            account_type=data.get("account_type", "savings"),
            is_active=data.get("is_active", True),
            is_primary=data.get("is_primary", False),
            notes=data.get("notes", ""),
            created_by=request.user,
        )
        return JsonResponse({"success": True, "id": bank.id, "message": "Bank account created"})

    def put(self, request):
        data = request.POST or request.data
        bank_id = data.get("id")
        
        if not bank_id:
            return JsonResponse({"success": False, "message": "Missing bank account ID"}, status=400)
        
        try:
            bank = BankAccount.objects.get(id=bank_id)
        except BankAccount.DoesNotExist:
            return JsonResponse({"success": False, "message": "Bank account not found"}, status=404)

        if data.get("bank_name"):
            bank.bank_name = data["bank_name"]
        if data.get("account_name"):
            bank.account_name = data["account_name"]
        if data.get("account_number"):
            bank.account_number = data["account_number"]
        if data.get("account_type"):
            bank.account_type = data["account_type"]
        if "is_active" in data:
            bank.is_active = data["is_active"] in ["true", "True", "1", True]
        if "is_primary" in data:
            bank.is_primary = data["is_primary"] in ["true", "True", "1", True]
        if data.get("notes") is not None:
            bank.notes = data["notes"]
            
        bank.save()
        return JsonResponse({"success": True, "message": "Bank account updated"})

    def delete(self, request):
        bank_id = request.GET.get("id")
        
        if not bank_id:
            return JsonResponse({"success": False, "message": "Missing bank account ID"}, status=400)
        
        try:
            bank = BankAccount.objects.get(id=bank_id)
            bank.delete()
            return JsonResponse({"success": True, "message": "Bank account deleted"})
        except BankAccount.DoesNotExist:
            return JsonResponse({"success": False, "message": "Bank account not found"}, status=404)