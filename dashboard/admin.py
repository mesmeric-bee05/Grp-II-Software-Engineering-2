from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AuditLog, Customer, InventoryItem, Order, OrderItem, Payment, Product, StaffUser, StockTransaction

@admin.register(StaffUser)
class StaffUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Aroma Delight role", {"fields": ("role", "phone", "last_seen_at")}),)
    list_display = ("username", "first_name", "last_name", "role", "is_active", "last_seen_at")
    list_filter = ("role", "is_active")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_available")
    list_filter = ("category", "is_available")
    search_fields = ("name", "description")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "status", "created_by", "customer")
    list_filter = ("status", "channel")
    search_fields = ("=id", "customer__name")

for model in [Customer, OrderItem, Payment, InventoryItem, StockTransaction, AuditLog]:
    admin.site.register(model)
