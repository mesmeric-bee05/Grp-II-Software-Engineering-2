from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("request-access/", views.request_access, name="request_access"),
    path("logout/", views.logout_view, name="logout"),
    path("health/", views.health, name="health"),
    path("manus-routes.json", views.routes_manifest, name="routes_manifest"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/new/", views.order_new, name="order_new"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/status/", views.order_status, name="order_status"),
    path("orders/<int:pk>/receipt/", views.receipt, name="receipt"),
    path("products/", views.product_list, name="product_list"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/toggle/", views.product_toggle, name="product_toggle"),
    path("inventory/", views.inventory, name="inventory"),
    path("inventory/<int:pk>/adjust/", views.inventory_adjust, name="inventory_adjust"),
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/new/", views.customer_create, name="customer_create"),
    path("customers/<int:pk>/edit/", views.customer_edit, name="customer_edit"),
    path("staff/", views.staff_list, name="staff_list"),
]
