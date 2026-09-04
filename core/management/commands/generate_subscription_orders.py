from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Subscription, MilkOrder, Customer

class Command(BaseCommand):
    help = 'Generate daily orders based on active subscriptions'

    def handle(self, *args, **kwargs):
        today = timezone.localdate()
        subs = Subscription.objects.filter(is_active=True)
        count = 0
        
        for sub in subs:
            # Check if order already exists for this customer today for this product
            exists = MilkOrder.objects.filter(
                customer=sub.customer,
                date=today,
                product_type=sub.product_type
            ).exists()
            
            if not exists:
                order = MilkOrder(
                    shopkeeper=sub.shopkeeper,
                    customer=sub.customer,
                    date=today,
                    product_type=sub.product_type,
                    placed_by="SHOPKEEPER"
                )
                
                if sub.product_type == "MILK":
                    order.brand = sub.brand
                    order.milk_type = sub.milk_type
                    order.pack_size = sub.pack_size
                    order.packets = sub.packets
                else:
                    order.quantity = sub.quantity
                    order.unit = sub.unit
                    order.rate = sub.rate
                
                order.save()
                count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully generated {count} orders for {today}'))
