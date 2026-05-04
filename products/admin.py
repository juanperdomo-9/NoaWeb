from django.contrib import admin
from .models import Product, ProductVariant, Order, OrderItem, ProductImage


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductVariantInline, ProductImageInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'color', 'size', 'quantity', 'price')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'email',
        'phone',
        'city',
        'total',
        'payment_method',
        'is_paid',
        'created_at'
    )

    list_filter = ('payment_method', 'is_paid', 'created_at')
    search_fields = ('name', 'email', 'phone')

    list_editable = ('is_paid',)

    readonly_fields = (
        'name',
        'email',
        'phone',
        'address',
        'city',
        'postal_code',
        'province',
        'document',
        'shipping',
        'payment_method',
        'total',
        'created_at',
    )

    fieldsets = (
        ("📦 Pedido", {
            'fields': ('id', 'created_at', 'is_paid', 'payment_method', 'total')
        }),
        ("👤 Cliente", {
            'fields': ('name', 'email', 'phone', 'document')
        }),
        ("📍 Dirección", {
            'fields': ('address', 'city', 'postal_code', 'province')
        }),
        ("🚚 Envío", {
            'fields': ('shipping',)
        }),
    )

    inlines = [OrderItemInline]


admin.site.register(ProductImage)
admin.site.register(ProductVariant)
admin.site.register(OrderItem)