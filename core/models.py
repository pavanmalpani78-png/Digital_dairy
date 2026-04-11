from django.db import models
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.contrib.auth.models import User


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


class Customer(models.Model):
    shopkeeper = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Customer panel login
    login_phone = models.CharField(max_length=15, null=True, blank=True)
    login_password = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = ('shopkeeper', 'login_phone')

    def __str__(self):
        return self.name


class DeliveryBoy(models.Model):
    shopkeeper = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)

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
    def base_price_half_liter(brand_code: str) -> Decimal:
        base = {
            "AMUL": Decimal("27"),
            "VIKAS": Decimal("26"),
            "SARASWATI": Decimal("27"),
            "AMAR": Decimal("26"),
        }
        return base.get(brand_code or "", Decimal("27"))

    def milk_rate_from_base(self) -> Decimal:
        base = self.base_price_half_liter(self.brand)
        factor = (D(self.pack_size, "0") / Decimal("0.5")) if self.pack_size else Decimal("0")
        return base * factor

    def save(self, *args, **kwargs):
        """
        ✅ Logic:
        - If product_type == MILK and pack_size+packets given -> packets system
        - Else -> quantity * rate for ANY product (including MILK liters mode)
        """
        if self.product_type == "MILK" and self.pack_size and self.packets:
            size = D(self.pack_size, "0")
            pkts = D(self.packets, "0")

            self.rate = self.milk_rate_from_base()   # per packet
            self.total_liters = pkts * size
            self.total = pkts * self.rate

            self.quantity = Decimal("0")
            self.unit = ""
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
