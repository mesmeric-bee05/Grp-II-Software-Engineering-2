from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from dashboard.models import Customer, InventoryItem, Order, OrderItem, Payment, Product, StaffUser

class Command(BaseCommand):
    help = "Create or update safe local demonstration data for the Aroma Delight dashboard."

    @transaction.atomic
    def handle(self, *args, **options):
        users = [
            ("manager", "manager@aromadelight.local", "Amina", "Manager", StaffUser.Roles.MANAGER),
            ("cashier", "cashier@aromadelight.local", "Nia", "Cashier", StaffUser.Roles.CASHIER),
            ("barista", "barista@aromadelight.local", "Jabali", "Barista", StaffUser.Roles.BARISTA),
            ("admin", "admin@aromadelight.local", "Aroma", "Admin", StaffUser.Roles.ADMIN),
        ]
        for username, email, first_name, last_name, role in users:
            user, created = StaffUser.objects.get_or_create(username=username, defaults={"email": email, "first_name": first_name, "last_name": last_name, "role": role})
            user.email, user.first_name, user.last_name, user.role = email, first_name, last_name, role
            user.is_staff = role == StaffUser.Roles.ADMIN
            user.is_superuser = role == StaffUser.Roles.ADMIN
            if created or not user.has_usable_password():
                user.set_password("AromaDemo!2026")
            user.save()
        products = [
            ("Cappuccino", Product.Categories.HOT, "Double espresso, velvet milk and a little cloud.", "250"),
            ("Latte", Product.Categories.HOT, "Smooth espresso with silky steamed milk.", "300"),
            ("Kenyan tea", Product.Categories.HOT, "Strong, bright and brewed to order.", "100"),
            ("Passion juice", Product.Categories.COLD, "Fresh, sharp and made in-house.", "180"),
            ("Blueberry muffin", Product.Categories.SNACK, "Soft crumb, bright berries, no fuss.", "180"),
            ("Chicken sandwich", Product.Categories.LIGHT, "Toasted bread, fresh greens and roast chicken.", "250"),
        ]
        for name, category, description, price in products:
            product, _ = Product.objects.update_or_create(name=name, defaults={"category": category, "description": description, "price": Decimal(price), "is_available": True})
            InventoryItem.objects.update_or_create(product=product, defaults={"quantity_on_hand": Decimal("24" if "tea" not in name.lower() else "4"), "reorder_level": Decimal("6"), "unit": "servings"})
        customer, _ = Customer.objects.get_or_create(phone="0700000000", defaults={"name": "Wanjiku Kamau", "email": "wanjiku@example.com"})
        manager = StaffUser.objects.get(username="manager")
        cashier = StaffUser.objects.get(username="cashier")
        products_by_name = {p.name: p for p in Product.objects.all()}
        if not Order.objects.exists():
            samples = [("Cappuccino", 2, Payment.Methods.MPESA, Order.Status.COMPLETED), ("Chicken sandwich", 1, Payment.Methods.CASH, Order.Status.READY), ("Latte", 1, Payment.Methods.CARD, Order.Status.PREPARING)]
            for name, quantity, method, status in samples:
                order=Order.objects.create(customer=customer, created_by=cashier, status=status)
                product=products_by_name[name]
                total=product.price*quantity
                OrderItem.objects.create(order=order, product=product, quantity=quantity, unit_price=product.price, line_total=total)
                Payment.objects.create(order=order, method=method, amount=total, status=Payment.Status.PAID, reference="DEMO-"+str(order.pk), recorded_by=manager)
        self.stdout.write(self.style.SUCCESS("Demo staff, menu, inventory and sample orders are ready."))
        self.stdout.write("Demo password for all seeded users: AromaDemo!2026")
