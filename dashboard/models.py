from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

class StaffUser(AbstractUser):
    class Roles(models.TextChoices):
        MANAGER = "MANAGER", "Manager"
        CASHIER = "CASHIER", "Cashier"
        BARISTA = "BARISTA", "Barista"
        ADMIN = "ADMIN", "System administrator"
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.CASHIER)
    phone = models.CharField(max_length=30, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def is_management(self):
        return self.role in {self.Roles.MANAGER, self.Roles.ADMIN}

    @property
    def is_operational(self):
        return self.role in {self.Roles.MANAGER, self.Roles.ADMIN, self.Roles.CASHIER, self.Roles.BARISTA}

class Product(models.Model):
    class Categories(models.TextChoices):
        HOT = "HOT", "Hot beverages"
        COLD = "COLD", "Cold beverages"
        SNACK = "SNACK", "Snacks"
        LIGHT = "LIGHT", "Light meals"
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=Categories.choices, default=Categories.HOT)
    description = models.CharField(max_length=240, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    notes = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PREPARING = "PREPARING", "Preparing"
        READY = "READY", "Ready"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
    class Channels(models.TextChoices):
        COUNTER = "COUNTER", "Counter"
        ONLINE = "ONLINE", "Online"
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    created_by = models.ForeignKey(StaffUser, on_delete=models.PROTECT, related_name="orders_created")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    channel = models.CharField(max_length=20, choices=Channels.choices, default=Channels.COUNTER)
    notes = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def total(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))

    def __str__(self):
        return f"Order #{self.pk}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("order", "product")

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.price
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)

class Payment(models.Model):
    class Methods(models.TextChoices):
        CASH = "CASH", "Cash"
        MPESA = "MPESA", "M-Pesa"
        CARD = "CARD", "Card"
        BANK = "BANK", "Bank transfer"
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="payment")
    method = models.CharField(max_length=20, choices=Methods.choices, default=Methods.CASH)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PAID)
    reference = models.CharField(max_length=80, blank=True)
    recorded_by = models.ForeignKey(StaffUser, on_delete=models.PROTECT, related_name="payments_recorded")
    recorded_at = models.DateTimeField(default=timezone.now)

class InventoryItem(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="inventory")
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0"))])
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=5, validators=[MinValueValidator(Decimal("0"))])
    unit = models.CharField(max_length=30, default="units")
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_low_stock(self):
        return self.quantity_on_hand <= self.reorder_level

class StockTransaction(models.Model):
    class Types(models.TextChoices):
        IN = "IN", "Stock in"
        OUT = "OUT", "Stock out"
        ADJUST = "ADJUST", "Adjustment"
    inventory = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=Types.choices)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    reason = models.CharField(max_length=240)
    recorded_by = models.ForeignKey(StaffUser, on_delete=models.PROTECT, related_name="stock_transactions")
    created_at = models.DateTimeField(default=timezone.now)

class AuditLog(models.Model):
    actor = models.ForeignKey(StaffUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_events")
    action = models.CharField(max_length=80)
    entity = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

class AccessRequest(models.Model):
    class Roles(models.TextChoices):
        MANAGER = "MANAGER", "Manager"
        CASHIER = "CASHIER", "Cashier"
        BARISTA = "BARISTA", "Barista"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending review"
        APPROVED = "APPROVED", "Approved"
        DECLINED = "DECLINED", "Declined"

    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    requested_role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.CASHIER)
    reason = models.CharField(max_length=240)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(StaffUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="access_requests_reviewed")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
