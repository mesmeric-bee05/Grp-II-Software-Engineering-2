from decimal import Decimal
import json
import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils.crypto import get_random_string
from dashboard.models import AccessRequest, AuditLog, InventoryItem, Order, OrderItem, Payment, Product, StaffUser

@pytest.mark.django_db
@override_settings(LOCAL_HTTP=False, PREVIEW_MODE=True, CSRF_COOKIE_SECURE=True, CSRF_COOKIE_SAMESITE="None")
def test_preview_login_sets_cross_site_csrf_cookie():
    client = pytest.importorskip("django.test").Client()
    response = client.get(reverse("login"))
    csrf_cookie = response.cookies["csrftoken"]
    assert csrf_cookie["secure"] is True
    assert csrf_cookie["samesite"] == "None"

@pytest.mark.django_db
def test_login_accepts_case_insensitive_username_and_work_email():
    StaffUser.objects.create_user(username="manager", email="manager@aromadelight.local", password="AromaDemo!2026", role=StaffUser.Roles.MANAGER)
    client = pytest.importorskip("django.test").Client()
    response = client.post(reverse("login"), {"username": "MANAGER@AROMADELIGHT.LOCAL", "password": "AromaDemo!2026"})
    assert response.status_code == 302
    assert response["Location"] == "/"

@pytest.mark.django_db
def test_public_landing_and_access_request_flow():
    client = pytest.importorskip("django.test").Client()
    assert client.get(reverse("dashboard")).status_code == 200
    response = client.post(reverse("request_access"), {"full_name": "QA Onboarding", "email": "qa-onboarding@example.com", "phone": "+254700000000", "requested_role": "CASHIER", "reason": "Counter operations"})
    assert response.status_code == 302
    assert AccessRequest.objects.filter(email="qa-onboarding@example.com", status=AccessRequest.Status.PENDING).exists()

@pytest.mark.django_db
class TestOrderIntegrity:
    def setup_method(self):
        self.cashier = StaffUser.objects.create_user(username="cashier", password=get_random_string(32), role=StaffUser.Roles.CASHIER)
        self.product = Product.objects.create(name="Cappuccino", category=Product.Categories.HOT, price=Decimal("250.00"))

    def test_order_total_is_server_calculated_from_catalogue_price(self):
        client = pytest.importorskip("django.test").Client()
        client.force_login(self.cashier)
        response = client.post(reverse("order_new"), {"items_json": json.dumps([{"product_id": self.product.pk, "quantity": 2}]), "payment_method": "CASH", "payment_status": "PAID", "payment_amount": "500.00", "payment_reference": "TEST-001", "notes": ""})
        assert response.status_code == 302
        order = Order.objects.get()
        assert order.total == Decimal("500.00")
        assert Payment.objects.get(order=order).amount == Decimal("500.00")
        assert AuditLog.objects.filter(action="CREATE", entity="Order", entity_id=str(order.pk)).exists()

@pytest.mark.django_db
class TestRoleProtection:
    def setup_method(self):
        self.cashier = StaffUser.objects.create_user(username="cashier", password=get_random_string(32), role=StaffUser.Roles.CASHIER)
        self.product = Product.objects.create(name="Tea", category=Product.Categories.HOT, price=Decimal("100.00"))
        self.inventory = InventoryItem.objects.create(product=self.product, quantity_on_hand=Decimal("5"), reorder_level=Decimal("2"))

    def test_cashier_cannot_mutate_inventory(self):
        client = pytest.importorskip("django.test").Client()
        client.force_login(self.cashier)
        response = client.post(reverse("inventory_adjust", args=[self.inventory.pk]), {"transaction_type": "IN", "quantity": "5", "reason": "Unauthorised test"})
        assert response.status_code == 403
        self.inventory.refresh_from_db()
        assert self.inventory.quantity_on_hand == Decimal("5")
