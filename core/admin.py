from django.contrib import admin
from .models import Customer, MilkOrder, MilkTransaction, DeliveryBoy, UPIPayment, ShopkeeperProfile, Notification, ShopSettings

admin.site.register(Customer)
admin.site.register(MilkOrder)
admin.site.register(MilkTransaction)
admin.site.register(DeliveryBoy)
admin.site.register(UPIPayment)
admin.site.register(ShopkeeperProfile)
admin.site.register(Notification)
admin.site.register(ShopSettings)