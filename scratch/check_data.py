import os
import django
from django.db.models import Sum, Q

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'khatabook.settings')
django.setup()

from core.models import Customer, MilkOrder, MilkTransaction

def check_customer_data():
    for customer in Customer.objects.all():
        print(f"Customer: {customer.name} (ID: {customer.id})")
        orders = MilkOrder.objects.filter(customer=customer)
        txns = MilkTransaction.objects.filter(customer=customer)
        
        print(f"  Orders ({orders.count()}):")
        for o in orders:
            print(f"    - {o.id}: {o.date} {o.product_type} {o.total}")
            
        print(f"  Transactions ({txns.count()}):")
        for t in txns:
            print(f"    - {t.id}: {t.date} {t.product_type} {t.amount}")

        order_totals = orders.aggregate(
            total_liters=Sum("total_liters"),
            total_qty=Sum("quantity"),
            total_amount=Sum("total"),
        )
        txn_totals = txns.aggregate(
            total_amount=Sum("amount"),
            total_liters=Sum("qty", filter=Q(product_type="MILK", unit="L")),
            total_qty=Sum("qty", filter=~Q(product_type="MILK", unit="L")),
        )
        
        print(f"  Aggregated Orders: {order_totals}")
        print(f"  Aggregated Trans: {txn_totals}")
        print("-" * 30)

if __name__ == "__main__":
    check_customer_data()
