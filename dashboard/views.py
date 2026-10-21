import json
from datetime import timedelta
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, F, Q, Sum, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from .forms import CustomerForm, InventoryAdjustForm, LoginForm, OrderForm, ProductForm
from .models import AuditLog, Customer, InventoryItem, Order, OrderItem, Payment, Product, StaffUser, StockTransaction
from .services import audit, roles_required

@require_GET
def health(request):
    return JsonResponse({"status": "ok", "service": "aroma-delight-dashboard"})

@require_GET
def routes_manifest(request):
    routes = [
        {"path": "/", "title": "Dashboard"}, {"path": "/login/", "title": "Staff login"},
        {"path": "/orders/", "title": "Orders"}, {"path": "/orders/new/", "title": "New order"},
        {"path": "/products/", "title": "Menu"}, {"path": "/inventory/", "title": "Inventory"},
        {"path": "/customers/", "title": "Customers"}, {"path": "/staff/", "title": "Staff"},
    ]
    return JsonResponse({"routes": routes})

@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        StaffUser.objects.filter(pk=form.get_user().pk).update(last_seen_at=timezone.now())
        next_url = request.POST.get("next") or request.GET.get("next") or reverse("dashboard")
        if not next_url.startswith("/") or next_url.startswith("//"):
            next_url = reverse("dashboard")
        return redirect(next_url)
    return render(request, "login.html", {"form": form, "next": request.GET.get("next", "")})

@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def dashboard(request):
    if not request.user.is_operational and not request.user.is_superuser:
        messages.error(request, "Your account is not assigned an operational role yet.")
    period = request.GET.get("period", "7d")
    today = timezone.localdate()
    days = {"today": 1, "7d": 7, "30d": 30}.get(period, 7)
    start = today - timedelta(days=days - 1)
    orders = Order.objects.filter(created_at__date__gte=start, created_at__date__lte=today).select_related("customer", "created_by")
    paid = Payment.objects.filter(order__in=orders, status=Payment.Status.PAID)
    revenue = paid.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    order_count = orders.exclude(status=Order.Status.CANCELLED).count()
    average_ticket = (revenue / order_count).quantize(Decimal("0.01")) if order_count else Decimal("0.00")
    low_stock = InventoryItem.objects.select_related("product").filter(quantity_on_hand__lte=F("reorder_level"))
    payment_mix_rows = paid.values("method").annotate(total=Sum("amount")).order_by("-total")
    payment_mix = [{"label": Payment.Methods(row["method"]).label, "total": row["total"] or Decimal("0.00"), "percent": int(((row["total"] or Decimal("0.00")) / revenue) * 100) if revenue else 0} for row in payment_mix_rows]
    top_products = list(OrderItem.objects.filter(order__in=orders).values("product__name").annotate(units=Sum("quantity")).order_by("-units")[:5])
    trend_qs = paid.annotate(day=TruncDate("recorded_at")).values("day").annotate(total=Sum("amount")).order_by("day")
    trend = {str(row["day"]): float(row["total"] or 0) for row in trend_qs}
    chart = [{"label": str(start + timedelta(days=i)), "value": trend.get(str(start + timedelta(days=i)), 0)} for i in range(days)]
    context = {"period": period, "revenue": revenue, "order_count": order_count, "average_ticket": average_ticket, "low_stock": low_stock[:6], "low_stock_count": low_stock.count(), "payment_mix": payment_mix, "top_products": top_products, "recent_orders": orders[:8], "chart_data": json.dumps(chart)}
    return render(request, "dashboard.html", context)

@login_required
def order_list(request):
    status = request.GET.get("status", "")
    orders = Order.objects.select_related("customer", "created_by").prefetch_related("items__product")
    if status in {choice[0] for choice in Order.Status.choices}:
        orders = orders.filter(status=status)
    return render(request, "orders.html", {"orders": orders[:100], "status": status, "status_choices": Order.Status.choices})

@roles_required(StaffUser.Roles.MANAGER, StaffUser.Roles.ADMIN, StaffUser.Roles.CASHIER)
def order_new(request):
    products = Product.objects.filter(is_available=True).order_by("category", "name")
    form = OrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        product_ids = [item["product_id"] for item in form.cleaned_data["items_json"]]
        product_map = {p.pk: p for p in Product.objects.filter(pk__in=product_ids, is_available=True)}
        if len(product_map) != len(set(product_ids)):
            form.add_error("items_json", "One or more selected products are no longer available.")
        else:
            with transaction.atomic():
                order = Order.objects.create(customer=form.cleaned_data["customer"], created_by=request.user, notes=form.cleaned_data["notes"])
                total = Decimal("0.00")
                for item in form.cleaned_data["items_json"]:
                    product = product_map[item["product_id"]]
                    line_total = product.price * item["quantity"]
                    total += line_total
                    OrderItem.objects.create(order=order, product=product, quantity=item["quantity"], unit_price=product.price, line_total=line_total)
                amount = form.cleaned_data["payment_amount"] or total
                if amount != total:
                    form.add_error("payment_amount", "Payment amount must equal the server-calculated order total.")
                    transaction.set_rollback(True)
                else:
                    Payment.objects.create(order=order, method=form.cleaned_data["payment_method"], amount=total, status=form.cleaned_data["payment_status"], reference=form.cleaned_data["payment_reference"], recorded_by=request.user)
                    audit(request, "CREATE", "Order", order.pk, {"item_count": len(product_ids), "total": str(total)})
                    messages.success(request, f"Order #{order.pk} created and ready for the barista queue.")
                    return redirect("order_detail", pk=order.pk)
    return render(request, "order_new.html", {"form": form, "products": products})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related("customer", "created_by").prefetch_related("items__product"), pk=pk)
    return render(request, "order_detail.html", {"order": order, "status_choices": Order.Status.choices})

@roles_required(StaffUser.Roles.MANAGER, StaffUser.Roles.ADMIN, StaffUser.Roles.CASHIER, StaffUser.Roles.BARISTA)
@require_POST
def order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get("status")
    allowed = {choice[0] for choice in Order.Status.choices}
    if new_status not in allowed:
        messages.error(request, "That order status is not recognised.")
    elif request.user.role == StaffUser.Roles.BARISTA and new_status not in {Order.Status.PREPARING, Order.Status.READY}:
        messages.error(request, "Baristas can move orders through preparation only.")
    else:
        old = order.status
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        audit(request, "STATUS_CHANGE", "Order", order.pk, {"from": old, "to": new_status})
        messages.success(request, f"Order #{order.pk} is now {order.get_status_display().lower()}.")
    return redirect(request.POST.get("next") or "order_detail", pk=pk)

@login_required
def receipt(request, pk):
    order = get_object_or_404(Order.objects.select_related("customer", "payment").prefetch_related("items__product"), pk=pk)
    return render(request, "receipt.html", {"order": order})

@roles_required(StaffUser.Roles.MANAGER, StaffUser.Roles.ADMIN)
def product_list(request):
    return render(request, "products.html", {"products": Product.objects.all()})

@roles_required(StaffUser.Roles.MANAGER, StaffUser.Roles.ADMIN)
def product_create(request):
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        InventoryItem.objects.get_or_create(product=product, defaults={"quantity_on_hand": 0, "reorder_level": 5})
        audit(request, "CREATE", "Product", product.pk, {"name": product.name})
        messages.success(request, f"{product.name} added to the menu.")
        return redirect("product_list")
    return render(request, "product_form.html", {"form": form, "title": "Add menu item"})

@roles_required(StaffUser.Roles.MANAGER, StaffUser.Roles.ADMIN)
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        audit(request, "UPDATE", "Product", product.pk, {"name": product.name})
        messages.success(request, f"{product.name} updated.")
        return redirect("product_list")
    return render(request, "product_form.html", {"form": form, "title": f"Edit {product.name}"})

@roles_required(StaffUser.Roles.MANAGER, StaffUser.Roles.ADMIN)
@require_POST
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_available = not product.is_available
    product.save(update_fields=["is_available", "updated_at"])
    audit(request, "TOGGLE_AVAILABILITY", "Product", product.pk, {"is_available": product.is_available})
    messages.success(request, f"{product.name} is now {'available' if product.is_available else 'hidden'}.")
    return redirect("product_list")

@login_required
def inventory(request):
    items = InventoryItem.objects.select_related("product").order_by("quantity_on_hand", "product__name")
    return render(request, "inventory.html", {"items": items, "low_count": items.filter(quantity_on_hand__lte=F("reorder_level")).count()})

@roles_required(StaffUser.Roles.MANAGER, StaffUser.Roles.ADMIN)
@require_POST
def inventory_adjust(request, pk):
    item = get_object_or_404(InventoryItem.objects.select_related("product"), pk=pk)
    form = InventoryAdjustForm(request.POST)
    if form.is_valid():
        transaction_type = form.cleaned_data["transaction_type"]
        qty = form.cleaned_data["quantity"]
        before = item.quantity_on_hand
        if transaction_type == "IN":
            after = before + qty
        elif transaction_type == "OUT":
            after = before - qty
        else:
            after = qty
        if after < 0:
            messages.error(request, "Stock cannot fall below zero.")
        else:
            with transaction.atomic():
                item.quantity_on_hand = after
                item.save(update_fields=["quantity_on_hand", "updated_at"])
                StockTransaction.objects.create(inventory=item, transaction_type=transaction_type, quantity=qty, reason=form.cleaned_data["reason"], recorded_by=request.user)
                audit(request, "STOCK_ADJUSTMENT", "InventoryItem", item.pk, {"before": str(before), "after": str(after), "type": transaction_type})
            messages.success(request, f"{item.product.name} stock updated to {after} {item.unit}.")
    else:
        messages.error(request, "Stock adjustment was not valid. Check the quantity and reason.")
    return redirect("inventory")

@login_required
def customer_list(request):
    query = request.GET.get("q", "").strip()
    customers = Customer.objects.all()
    if query:
        customers = customers.filter(Q(name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query))
    return render(request, "customers.html", {"customers": customers, "query": query})

@roles_required(StaffUser.Roles.MANAGER, StaffUser.Roles.ADMIN, StaffUser.Roles.CASHIER)
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        customer = form.save()
        audit(request, "CREATE", "Customer", customer.pk, {"name": customer.name})
        messages.success(request, f"{customer.name} added to customer records.")
        return redirect("customer_list")
    return render(request, "customer_form.html", {"form": form, "title": "Add customer"})

@roles_required(StaffUser.Roles.MANAGER, StaffUser.Roles.ADMIN, StaffUser.Roles.CASHIER)
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        customer = form.save()
        audit(request, "UPDATE", "Customer", customer.pk, {"name": customer.name})
        messages.success(request, f"{customer.name} updated.")
        return redirect("customer_list")
    return render(request, "customer_form.html", {"form": form, "title": f"Edit {customer.name}"})

@roles_required(StaffUser.Roles.MANAGER, StaffUser.Roles.ADMIN)
def staff_list(request):
    return render(request, "staff.html", {"staff": StaffUser.objects.order_by("role", "last_name", "username"), "audit_events": AuditLog.objects.select_related("actor")[:10]})
