from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Customer
from .utils import send_automated_whatsapp
from django.conf import settings

@receiver(post_save, sender=Customer)
def send_welcome_whatsapp(sender, instance, created, **kwargs):
    if created:
        if instance.phone:
            shopkeeper = instance.shopkeeper
            shop_profile = getattr(shopkeeper, 'profile', None)
            shop_code = shop_profile.shop_code if shop_profile else "Not Set"
            
            # Construct the login link
            # We assume a fixed host if not passed in request, or use localhost for dev
            host = getattr(settings, 'RENDER_EXTERNAL_HOSTNAME', '127.0.0.1:8000')
            protocol = "https" if getattr(settings, 'RENDER_EXTERNAL_HOSTNAME', None) else "http"
            login_link = f"{protocol}://{host}/c/login/"
            
            message = (
                f"Hey {instance.name}, welcome to our dairy!\n\n"
                f"You can now place milk orders online here: {login_link}\n\n"
                f"*Your Login Credentials:*\n"
                f"Shop Code: {shop_code}\n"
                f"Phone: {instance.login_phone}\n"
                f"Password: {instance.login_password}\n\n"
                f"Thank you!"
            )
            
            send_automated_whatsapp(shopkeeper, instance.phone, message)
