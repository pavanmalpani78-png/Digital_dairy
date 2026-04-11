import re

with open('core/views.py', 'r', encoding='utf8') as f:
    text = f.read()

text = text.replace('from django.contrib import messages', 'from django.contrib import messages\nfrom django.contrib.auth import authenticate, login, logout\nfrom django.contrib.auth.models import User\nfrom django.contrib.auth.decorators import login_required')

for func in ['dashboard', 'customer_page', 'add_customer', 'edit_customer', 'delete_customer', 'milk_order', 'edit_order', 'delete_order', 'transaction_page', 'add_transaction', 'daily_milk_report', 'shop_pending_orders', 'approve_order', 'reject_order', 'shop_delivery_dashboard', 'bill_select_customer', 'bill_view', 'bill_pdf']:
    text = text.replace(f'def {func}(request', f'@login_required\ndef {func}(request')

text = text.replace('Customer.objects.all()', 'Customer.objects.filter(shopkeeper=request.user)')
text = text.replace('get_object_or_404(Customer, id=id)', 'get_object_or_404(Customer, id=id, shopkeeper=request.user)')
text = text.replace('get_object_or_404(MilkOrder, pk=pk)', 'get_object_or_404(MilkOrder, pk=pk, shopkeeper=request.user)')
text = text.replace('.objects.filter(date=selected_date)', '.objects.filter(shopkeeper=request.user, date=selected_date)')
text = text.replace('placed_by="CUSTOMER", status="PENDING"', 'shopkeeper=request.user, placed_by="CUSTOMER", status="PENDING"')
text = text.replace('DeliveryBoy.objects.filter(is_active=True)', 'DeliveryBoy.objects.filter(shopkeeper=request.user, is_active=True)')
text = text.replace('MilkTransaction.objects.select_related', 'MilkTransaction.objects.filter(shopkeeper=request.user).select_related')

with open('core/views.py', 'w', encoding='utf8') as f:
    f.write(text)
