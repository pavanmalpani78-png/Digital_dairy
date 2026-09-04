import threading
import requests
from .models import ShopSettings

def send_ultramsg_message_sync(instance_id, token, phone, message):
    """Synchronous function to make the API call to UltraMsg"""
    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    
    # Ensure phone has no plus and includes country code
    phone = phone.strip()
    if not phone.startswith('+') and len(phone) == 10:
        phone = "91" + phone
    phone = phone.replace('+', '')
        
    payload = {
        "token": token,
        "to": phone,
        "body": message
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        # Log response or handle errors if needed
        # print("UltraMsg Response:", response.text)
    except Exception as e:
        # Catch network errors to avoid crashing the server
        print(f"Failed to send WhatsApp message: {str(e)}")

def send_automated_whatsapp(shopkeeper, phone, message):
    """
    Checks if shopkeeper has WhatsApp enabled and valid settings.
    Dispatches a background thread to send the message via UltraMsg.
    """
    if not phone:
        return
        
    try:
        settings = ShopSettings.objects.get(shopkeeper=shopkeeper)
        if settings.is_whatsapp_enabled and settings.whatsapp_instance_id and settings.whatsapp_token:
            # Dispatch as a background thread so it doesn't slow down the website!
            thread = threading.Thread(
                target=send_ultramsg_message_sync,
                args=(settings.whatsapp_instance_id, settings.whatsapp_token, phone, message)
            )
            thread.start()
    except ShopSettings.DoesNotExist:
        pass
