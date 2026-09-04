from django.db import models
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.contrib.auth.models import User
import re
import uuid


PRODUCT_TYPES = (
    ("MILK", "Milk"),
    ("GHEE", "Ghee"),
    ("PANEER", "Paneer"),
    ("CURD", "Curd"),
    ("BUTTER", "Butter"),
)

def D(x, default="0"):
    """Safe Decimal converter."""
    try:
        if x is None:
            return Decimal(default)
        x = str(x).strip()
        if x == "":
            return Decimal(default)
        return Decimal(x)
    except (InvalidOperation, ValueError):
        return Decimal(default)




class ShopkeeperProfile(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    shop_name  = models.CharField(max_length=100, blank=True, default='')
    shop_address = models.TextField(blank=True, default='')
    phone      = models.CharField(max_length=15, blank=True, default='')
    # Unique code customers use to identify their shop at login
    shop_code  = models.CharField(max_length=50, unique=True, blank=True,
                                  help_text='Auto-filled from username. Share this with your customers.')

    def save(self, *args, **kwargs):
        # Auto-generate shop_code from username if not set
        if not self.shop_code:
            base = re.sub(r'[^a-z0-9_]', '', self.user.username.lower())
            self.shop_code = base or f'shop{self.user.id}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.shop_name or self.user.username


class Customer(models.Model):
    shopkeeper = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Customer panel login
    login_phone    = models.CharField(max_length=15, null=True, blank=True)
    login_password = models.CharField(max_length=50, null=True, blank=True)
    # Shopkeeper can disable a customer's login access
    is_active      = models.BooleanField(default=True, help_text='Uncheck to block this customer from logging in.')

    class Meta:
        unique_together = ('shopkeeper', 'login_phone')

    def __str__(self):
        return self.name


class DeliveryBoy(models.Model):
    shopkeeper = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    access_token = models.UUIDField(default=uuid.uuid4, null=True, blank=True)

    class Meta:
        unique_together = ('shopkeeper', 'phone')

    def __str__(self):
        return self.name


class UPIPayment(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("VERIFIED", "Verified"),
        ("FAILED", "Failed"),
    )
    shopkeeper = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True, help_text="12-digit UTR or Transaction ID")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} - ₹{self.amount} - {self.status}"


class MilkOrder(models.Model):
    MILK_BRANDS = (
        ("AMUL", "Amul"),
        ("VIKAS", "Vikas"),
        ("SARASWATI", "Saraswati"),
        ("AMAR", "Amar"),
    )

    MILK_TYPES = (
        ("COW", "Cow Milk"),
        ("BUFFALO", "Buffalo Milk"),
    )

    PLACED_BY = (
        ("SHOPKEEPER", "Shopkeeper"),
        ("CUSTOMER", "Customer"),
    )

    STATUS = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    PAYMENT_METHODS = (
        ("COD", "Cash on Delivery"),
        ("ONLINE_UPI", "Online UPI"),
    )

    shopkeeper = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default="MILK")
    placed_by = models.CharField(max_length=20, choices=PLACED_BY, default="SHOPKEEPER")
    status = models.CharField(max_length=20, choices=STATUS, default="APPROVED")

    # Delivery tracking fields
    DELIVERY_STATUS = (
        ("PENDING", "Pending"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
    )
    delivery_boy = models.ForeignKey(DeliveryBoy, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default="PENDING")
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default="COD")

    # Payment Status
    PAYMENT_STATUS = (
        ("UNPAID", "Unpaid"),
        ("PAID", "Paid"),
    )
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="UNPAID")

    # milk-only optional fields
    brand = models.CharField(max_length=20, choices=MILK_BRANDS, blank=True, null=True)
    milk_type = models.CharField(max_length=10, choices=MILK_TYPES, blank=True, null=True)
    pack_size = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)  # 0.5/1/2/5
    packets = models.PositiveIntegerField(default=0)

    # generic fields for all products
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    unit = models.CharField(max_length=10, default="")  # L / KG / PCS
    rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    total_liters = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    date = models.DateField(default=timezone.localdate)

    def __str__(self):
        return f"{self.customer.name} - {self.product_type} - {self.total}"

    @staticmethod
    def base_price_half_liter(brand_code: str, milk_type: str) -> Decimal:
        # Base price per 0.5 liter
        if milk_type == "COW":
            return Decimal("27")  # Cow is always 27 for 0.5L
        elif milk_type == "BUFFALO":
            return Decimal("37") if brand_code == "VIKAS" else Decimal("35")
        return Decimal("35")  # Default fallback

    def milk_rate_from_base(self) -> Decimal:
        base = self.base_price_half_liter(self.brand, self.milk_type)
        factor = (D(self.pack_size, "0") / Decimal("0.5")) if self.pack_size else Decimal("0")
        return base * factor

    def save(self, *args, **kwargs):
        """
        ✅ Logic:
        - If pack_size+packets given -> packets system for ANY product
        - Else -> quantity * rate for ANY product (including MILK liters mode)
        """
        # Auto-fill missing rate for non-MILK products to prevent 0 balance
        if self.product_type != "MILK" and D(self.rate, "0") == Decimal("0") and getattr(self, 'customer_id', None):
            last_order = MilkOrder.objects.filter(
                customer_id=self.customer_id,
                product_type=self.product_type,
                rate__gt=0
            ).order_by('-date', '-id').first()
            if last_order:
                self.rate = last_order.rate

        if self.pack_size and self.packets:
            size = D(self.pack_size, "0")
            pkts = D(self.packets, "0")

            if self.product_type == "MILK":
                self.rate = self.milk_rate_from_base()   # per packet
                self.total_liters = pkts * size
                self.quantity = Decimal("0")
                self.unit = ""
            else:
                self.rate = D(self.rate, "0")
                self.total_liters = Decimal("0")
                self.quantity = pkts * size
                if not self.unit:
                    self.unit = "KG"

            self.total = pkts * self.rate
        else:
            q = D(self.quantity, "0")
            r = D(self.rate, "0")
            self.total = q * r

            if self.product_type == "MILK":
                self.total_liters = q
                if not self.unit:
                    self.unit = "L"
            else:
                self.total_liters = Decimal("0")

        super().save(*args, **kwargs)


class MilkTransaction(models.Model):
    PAYMENT_STATUS = (
        ("PAID", "Paid"),
        ("UNPAID", "Unpaid"),
    )

    UNIT_CHOICES = (
        ("L", "Liters"),
        ("KG", "Kilogram"),
        ("PCS", "Pieces"),
    )

    shopkeeper = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default="MILK")

    qty = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default="L")

    rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default="UNPAID")
    date = models.DateField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.amount = D(self.qty, "0") * D(self.rate, "0")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.name} - {self.payment_status} - {self.amount}"


class Notification(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.customer.name}"


class ShopSettings(models.Model):
    shopkeeper = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop_settings')
    whatsapp_instance_id = models.CharField(max_length=255, blank=True, null=True, help_text="UltraMsg Instance ID")
    whatsapp_token = models.CharField(max_length=255, blank=True, null=True, help_text="UltraMsg Token")
    is_whatsapp_enabled = models.BooleanField(default=False)
    upi_id = models.CharField(max_length=50, blank=True, null=True, help_text="UPI ID for dynamic QR codes on bills")

    def __str__(self):
        return f"Settings for {self.shopkeeper.username}"

class Expense(models.Model):
    EXPENSE_CATEGORIES = (
        ("MILK_PURCHASE", "Milk Purchase"),
        ("SALARY", "Salary"),
        ("TRANSPORT", "Transport"),
        ("FODDER", "Fodder"),
        ("ELECTRICITY", "Electricity"),
        ("MAINTENANCE", "Maintenance"),
        ("OTHER", "Other"),
    )
    shopkeeper = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES, default="OTHER")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.category} - ₹{self.amount} ({self.date})"


class Subscription(models.Model):
    shopkeeper = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(default=timezone.localdate)
    
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default="MILK")
    brand = models.CharField(max_length=20, choices=MilkOrder.MILK_BRANDS, blank=True, null=True)
    milk_type = models.CharField(max_length=10, choices=MilkOrder.MILK_TYPES, blank=True, null=True)
    pack_size = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    packets = models.PositiveIntegerField(default=0)
    
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    unit = models.CharField(max_length=10, default="L")
    rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return f"Sub: {self.customer.name} - {self.product_type}"
