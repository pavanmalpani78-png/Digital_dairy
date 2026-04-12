
from django import forms
from .models import Customer, MilkOrder, MilkTransaction


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "address", "login_phone", "login_password"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2}),
            "login_password": forms.PasswordInput(render_value=True),
        }



from django import forms
from .models import MilkTransaction

class MilkTransactionForm(forms.ModelForm):
    class Meta:
        model = MilkTransaction
        fields = ["customer", "product_type", "qty", "unit", "rate", "payment_status", "note"]


        widgets = {
            "customer": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "payment_status": forms.Select(attrs={"class": "form-select"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


        
        
