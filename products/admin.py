from django.contrib import admin
from .models import Product, ProductVariant, Order, OrderItem, ProductImage

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductVariantInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'total', 'created_at')
    inlines = [OrderItemInline]


admin.site.register(OrderItem)
admin.site.register(ProductImage)