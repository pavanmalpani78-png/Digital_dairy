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



class MilkTransactionForm(forms.ModelForm):
    class Meta:
        model = MilkTransaction
        fields = ["customer", "product_type", "qty", "unit", "rate", "payment_status"]

        widgets = {
            "customer": forms.Select(attrs={"class": "form-select"}),
            "qty": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "payment_status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['customer'].queryset = Customer.objects.filter(shopkeeper=user).order_by('name')


        
        