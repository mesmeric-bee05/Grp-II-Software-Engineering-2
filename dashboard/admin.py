from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AccessRequest, AuditLog, Customer, InventoryItem, Order, OrderItem, Payment, Product, StaffUser, StockTransaction

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

@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "requested_role", "status", "created_at", "reviewed_by")
    list_filter = ("status", "requested_role")
    search_fields = ("full_name", "email", "phone")
    readonly_fields = ("created_at",)

for model in [Customer, OrderItem, Payment, InventoryItem, StockTransaction, AuditLog]:
    admin.site.register(model)
